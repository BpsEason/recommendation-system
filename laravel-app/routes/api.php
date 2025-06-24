<?php

use App\Http\Middleware\AssignRecommendationGroup;
use App\Services\RecommendationService;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Events\RecommendationInteraction;
use Illuminate\Support\Facades\Auth;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
|
| Here is where you can register API routes for your application. These
| routes are loaded by the RouteServiceProvider within a group which
| is assigned the "api" middleware group. Enjoy building your API!
|
*/

Route::middleware('auth:sanctum')->get('/user', function (Request $request) {
    return $request->user();
});

Route::middleware([AssignRecommendationGroup::class])->get('/user/recommendations', function (Request $request, RecommendationService $recommendationService) {
    $userId = $request->attributes->get('current_user_id');
    $assignedGroup = $request->attributes->get('recommendation_group');
    $experimentName = $request->attributes->get('recommendation_experiment');

    $recommendations = $recommendationService->getRecommendations($userId, $assignedGroup);

    event(new RecommendationInteraction(
        userId: $userId,
        experimentName: $experimentName,
        group: $assignedGroup,
        action: 'impression',
        productId: null,
        metadata: ['recommended_ids' => array_column($recommendations, 'id')]
    ));

    return response()->json([
        'user_id' => $userId,
        'recommendations' => $recommendations,
        'assigned_group' => $assignedGroup,
    ]);
});

Route::middleware([])->post('/track/click', function (Request $request) {
    $request->validate([
        'product_id' => 'required|integer',
        'group' => 'required|string',
        'experiment_name' => 'required|string',
    ]);

    $userId = Auth::id() ?? 0;
    $productId = $request->input('product_id');
    $group = $request->input('group');
    $experimentName = $request->input('experiment_name');

    event(new RecommendationInteraction(
        userId: $userId,
        experimentName: $experimentName,
        group: $group,
        action: 'click',
        productId: $productId,
        metadata: []
    ));

    return response()->json(['status' => 'success', 'message' => 'Click tracked.']);
});
