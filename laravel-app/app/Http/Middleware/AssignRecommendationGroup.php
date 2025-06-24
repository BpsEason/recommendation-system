<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Cache;

class AssignRecommendationGroup
{
    public function handle(Request $request, Closure $next)
    {
        $userId = Auth::id();
        $experimentName = 'default_recommendation_experiment';
        $experimentConfig = config('ab_test.experiments.' . $experimentName);

        if (!isset($experimentConfig['enabled']) || !$experimentConfig['enabled']) {
            $assignedGroup = $experimentConfig['default_group'] ?? 'control';
            Log::info("Recommendation experiment '{$experimentName}' is disabled or not configured. User {$userId} assigned to default group: {$assignedGroup}");
        } else {
            if (!$userId) {
                // For guest users, assign a consistent guest ID for tracking
                $guestId = session()->getId();
                $assignedGroup = $this->assignGroupWithWeight($guestId, $experimentConfig['groups'], config('ab_test.salt'));
                // Store guest group in session
                session(['recommendation_group' => $assignedGroup]);
                Log::info("Guest user {$guestId} assigned to group: {$assignedGroup}.");
                $userId = 0; // Use 0 for logging guest interactions in 'user_id' field, if user_id is nullable in DB
            } else {
                $user = Auth::user();
                $assignedGroup = $user->recommendation_group;

                if (!$assignedGroup) {
                    $assignedGroup = $this->assignGroupWithThompsonSampling($userId, $experimentName, $experimentConfig['groups']);
                    $user->recommendation_group = $assignedGroup;
                    $user->save();
                    Log::info("User {$userId} assigned to recommendation group: {$assignedGroup} via Thompson Sampling and saved to DB.");
                } else {
                    Log::info("User {$userId} already has recommendation group: {$assignedGroup} from DB.");
                }
            }
        }

        $request->attributes->set('recommendation_group', $assignedGroup);
        $request->attributes->set('recommendation_experiment', $experimentName);
        $request->attributes->set('current_user_id', $userId); // Pass normalized user ID (0 for guest)

        return $next($request);
    }

    protected function assignGroupWithThompsonSampling(int $userId, string $experimentName, array $groupsConfig): string
    {
        $groupStats = Cache::remember("mab_stats:{$experimentName}", 300, function () use ($experimentName) {
            return DB::table('recommendation_events')
                ->where('experiment_name', $experimentName)
                ->groupBy('group')
                ->select(
                    'group',
                    DB::raw('SUM(CASE WHEN action = "click" THEN 1 ELSE 0 END) as successes'),
                    DB::raw('COUNT(*) as trials')
                )
                ->get()
                ->keyBy('group');
        });

        $maxSample = -1;
        $selectedGroup = array_key_first($groupsConfig);

        foreach ($groupsConfig as $group => $initialWeight) {
            $stats = $groupStats->get($group, (object)['successes' => 0, 'trials' => 0]);
            $alpha = $stats->successes + 1;
            $beta = ($stats->trials - $stats->successes) + 1;

            // Simplified sampling: mean + some noise
            $sample = ($alpha / ($alpha + $beta)) * (1 + (mt_rand() / mt_getrandmax() - 0.5) * 0.1);

            if ($sample > $maxSample) {
                $maxSample = $sample;
                $selectedGroup = $group;
            }
        }

        if ($groupStats->isEmpty() || array_sum(array_values($groupsConfig)) !== 100) {
            Log::warning("MAB data empty or group weights don't sum to 100. Falling back to weighted random assignment for user {$userId}.");
            return $this->assignGroupWithWeight($userId, $groupsConfig, config('ab_test.salt'));
        }

        return $selectedGroup;
    }

    protected function assignGroupWithWeight(string $identifier, array $groupsConfig, string $salt): string
    {
        $hash = crc32($identifier . $salt);
        $percentage = ($hash % 100) + 1;

        $cumulativePercentage = 0;
        foreach ($groupsConfig as $group => $weight) {
            $weight = is_numeric($weight) ? (int) $weight : 0;
            $cumulativePercentage += $weight;
            if ($percentage <= $cumulativePercentage) {
                return $group;
            }
        }
        return array_key_first($groupsConfig);
    }
}
