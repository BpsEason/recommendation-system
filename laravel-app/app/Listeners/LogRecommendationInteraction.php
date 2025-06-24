<?php

namespace App\Listeners;

use App\Events\RecommendationInteraction;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;

class LogRecommendationInteraction implements ShouldQueue
{
    use InteractsWithQueue;

    public function __construct()
    {
        //
    }

    public function handle(RecommendationInteraction $event): void
    {
        try {
            DB::table('recommendation_events')->insert([
                'user_id' => $event->userId,
                'experiment_name' => $event->experimentName,
                'group' => $event->group,
                'action' => $event->action,
                'product_id' => $event->productId,
                'metadata' => json_encode($event->metadata),
                'created_at' => now(),
                'updated_at' => now(),
            ]);
            Log::info("Recommendation interaction logged successfully.", [
                'user_id' => $event->userId,
                'action' => $event->action,
                'product_id' => $event->productId,
                'group' => $event->group
            ]);
        } catch (\Exception $e) {
            Log::error("Failed to log recommendation interaction: " . $e->getMessage(), [
                'user_id' => $event->userId,
                'action' => $event->action,
                'product_id' => $event->productId,
                'error' => $e->getTraceAsString()
            ]);
        }
    }
}
