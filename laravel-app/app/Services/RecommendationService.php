<?php

namespace App\Services;

use GuzzleHttp\Client;
use GuzzleHttp\Exception\RequestException;
use Illuminate\Support\Facades\Log;
use App\Models\Product; // 引入 Product 模型

class RecommendationService
{
    protected Client $httpClient;
    protected string $recommendationApiUrl;

    public function __construct()
    {
        $this->recommendationApiUrl = config('app.recommendation_api_url', 'http://fastapi-recommender:8000');
        $this->httpClient = new Client([
            'base_uri' => $this->recommendationApiUrl,
            'timeout' => 5.0,
        ]);
    }

    public function getRecommendations(int $userId, string $strategyVersion = 'v1'): array
    {
        try {
            Log::info("Requesting recommendations for user $userId with strategy $strategyVersion from FastAPI service: " . $this->recommendationApiUrl);
            $response = $this->httpClient->get("/recommend/$userId", [
                'query' => ['strategy_version' => $strategyVersion]
            ]);

            $data = json_decode($response->getBody()->getContents(), true);

            $recommendedProductIds = $data['recommended_product_ids'] ?? [];
            
            // 從 Laravel 的資料庫讀取真實的產品詳細資訊，並篩選出上架狀態的商品
            $recommendations = Product::whereIn('id', $recommendedProductIds)
                                     ->active() // 只獲取上架的商品
                                     ->get(['id', 'name', 'price', 'category_id', 'image_url'])
                                     ->toArray();

            // 確保推薦順序與 FastAPI 返回的順序一致 (可選，但通常有用)
            $orderedRecommendations = [];
            foreach ($recommendedProductIds as $id) {
                foreach ($recommendations as $product) {
                    if ($product['id'] == $id) {
                        $orderedRecommendations[] = $product;
                        break;
                    }
                }
            }

            Log::info("Received and filtered recommendations for user $userId.", ['recommendations' => $orderedRecommendations]);

            return $orderedRecommendations;
        } catch (RequestException $e) {
            Log::error("Failed to get recommendations from FastAPI service: " . $e->getMessage(), [
                'user_id' => $userId,
                'strategy_version' => $strategyVersion,
                'exception' => $e->getTraceAsString(),
                'response' => $e->hasResponse() ? $e->getResponse()->getBody()->getContents() : 'No response'
            ]);
            // Fallback to popular active items or empty array
            // TODO: 在這裡可以實作從資料庫獲取熱門商品作為備用
            return Product::active()->inRandomOrder()->limit(10)->get(['id', 'name', 'price', 'category_id', 'image_url'])->toArray();
        } catch (\Exception $e) {
            Log::error("An unexpected error occurred while getting recommendations: " . $e->getMessage(), [
                'user_id' => $userId,
                'exception' => $e->getTraceAsString()
            ]);
            return Product::active()->inRandomOrder()->limit(10)->get(['id', 'name', 'price', 'category_id', 'image_url'])->toArray();
        }
    }
}
