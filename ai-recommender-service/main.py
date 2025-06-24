import os
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from recommender import Recommender
from prometheus_client import make_wsgi_app, Counter, Histogram, Gauge
from starlette.middleware.wsgi import WSGIMiddleware
import time
import json
import redis
from collections import Counter as PyCounter
from math import log2
from apscheduler.schedulers.asyncio import AsyncIOScheduler # 新增
import asyncio # 新增

# 初始化 FastAPI 應用 
app = FastAPI(title="AI Recommendation Service", version="1.0.0")

# 將 Prometheus 指標暴露在 /metrics 路徑 
app.mount("/metrics", WSGIMiddleware(make_wsgi_app()))

# 初始化推薦器實例 (這會在應用啟動時載入模型或訓練啞模型)
recommender_instance = Recommender()

# 初始化 Prometheus 指標
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests', ['endpoint'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP Request Latency', ['endpoint'])
RECOMMENDATION_SUCCESS_TOTAL = Counter('recommendation_success_total', 'Total successful recommendations', ['endpoint', 'strategy_version'])
RECOMMENDATION_PRODUCT_COUNT = Histogram('recommendation_product_count', 'Number of products in recommendation list', ['endpoint', 'strategy_version'], buckets=[5, 10, 15, 20, 25])
RECOMMENDATION_CATEGORY_DIVERSITY = Histogram('recommendation_category_diversity', 'Number of Unique Categories in Recommendations', ['endpoint', 'strategy_version'], buckets=[1, 2, 3, 4, 5, 10, 20])
RECOMMENDATION_ENTROPY = Gauge('recommendation_entropy', 'Entropy of Recommendation Distribution', ['endpoint', 'strategy_version'])
RECOMMENDATION_REPETITION_RATIO = Gauge('recommendation_repetition_ratio', 'Ratio of Repeated Products in Consecutive Recommendations', ['endpoint', 'strategy_version'])
RECOMMENDATION_COLD_START_TOTAL = Counter('recommendation_cold_start_total', 'Total Cold Start Recommendations', ['endpoint', 'strategy_version'])
RECOMMENDATION_CATALOG_COVERAGE = Gauge('recommendation_catalog_coverage_ratio', 'Ratio of Unique Products Recommended vs Total Catalog', ['endpoint', 'strategy_version'])

# Redis client for repetition tracking and catalog coverage (ensure it's initialized correctly)
try:
    redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=int(os.getenv('REDIS_PORT', 6379)), db=0)
    redis_client.ping()
    print("Successfully connected to Redis.")
except redis.exceptions.ConnectionError as e:
    print(f"Could not connect to Redis: {e}. Some metrics might be affected.")
    redis_client = None

RECOMMENDED_PRODUCTS_SET_KEY_PREFIX = "all_recommended_products"

# APScheduler 設定
scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup_event():
    # 在應用啟動時啟動模型訓練/更新的定時任務
    # 每 6 小時重新訓練模型
    scheduler.add_job(recommender_instance.train_and_save_model, 'interval', hours=6, id='model_retrain_job')
    # 每小時同步產品數據（包括上下架狀態）
    scheduler.add_job(recommender_instance.update_product_data, 'interval', hours=1, id='product_data_sync_job')
    scheduler.start()
    print("Scheduler started for model retraining and data synchronization.")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    print("Scheduler shut down.")

class RecommendationResponse(BaseModel):
    user_id: int
    recommended_product_ids: list[int]

@app.get("/health", summary="Health Check")
async def health_check():
    REQUEST_COUNT.labels(endpoint='/health').inc()
    return {"status": "ok"}

@app.get("/recommend/{user_id}", response_model=RecommendationResponse, summary="Get Product Recommendations")
async def get_recommendations(user_id: int, strategy_version: str = 'v1'):
    if user_id < 0:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    start_time = time.time()
    endpoint = f"/recommend/{{user_id}}"
    REQUEST_COUNT.labels(endpoint=endpoint).inc()

    try:
        recommended_product_ids = recommender_instance.get_recommendations(user_id, strategy_version)

        RECOMMENDATION_SUCCESS_TOTAL.labels(endpoint=endpoint, strategy_version=strategy_version).inc()
        RECOMMENDATION_PRODUCT_COUNT.labels(endpoint=endpoint, strategy_version=strategy_version).observe(len(recommended_product_ids))

        if recommended_product_ids and recommender_instance.products:
            categories = {recommender_instance.products.get(pid, {}).get('category_id', 'unknown') for pid in recommended_product_ids if pid in recommender_instance.products}
            RECOMMENDATION_CATEGORY_DIVERSITY.labels(endpoint=endpoint, strategy_version=strategy_version).observe(len(categories))

            category_counts = PyCounter()
            for pid in recommended_product_ids:
                cat = recommender_instance.products.get(pid, {}).get('category_id', 'unknown')
                category_counts[cat] += 1
            
            total_items = len(recommended_product_ids)
            entropy = 0
            if total_items > 0:
                for count in category_counts.values():
                    if count > 0:
                        probability = count / total_items
                        entropy -= probability * log2(probability)
            RECOMMENDATION_ENTROPY.labels(endpoint=endpoint, strategy_version=strategy_version).set(entropy)

            if redis_client:
                last_recommendations_key = f"last_recommendations:{user_id}:{strategy_version}"
                last_recommendations_json = redis_client.get(last_recommendations_key)
                
                last_recommendations = set(json.loads(last_recommendations_json) if last_recommendations_json else [])
                current_set = set(recommended_product_ids)
                
                overlap = len(last_recommendations.intersection(current_set))
                repetition_ratio = overlap / len(current_set) if current_set else 0

                RECOMMENDATION_REPETITION_RATIO.labels(endpoint=endpoint, strategy_version=strategy_version).set(repetition_ratio)
                redis_client.setex(last_recommendations_key, 3600, json.dumps(recommended_product_ids))

                redis_client.sadd(f"{RECOMMENDED_PRODUCTS_SET_KEY_PREFIX}:{strategy_version}", *recommended_product_ids)
                unique_recommended_count = redis_client.scard(f"{RECOMMENDED_PRODUCTS_SET_KEY_PREFIX}:{strategy_version}")
                total_products_in_catalog = len([pid for pid, info in recommender_instance.products.items() if info.get('status') == 'active']) # 只計算活躍商品
                if total_products_in_catalog > 0:
                    coverage_ratio = unique_recommended_count / total_products_in_catalog
                    RECOMMENDATION_CATALOG_COVERAGE.labels(endpoint=endpoint, strategy_version=strategy_version).set(coverage_ratio)
            else:
                print("Redis client not available, skipping repetition and catalog coverage metrics.")

        if user_id == 0 or (user_id % 2 == 0 and strategy_version == 'v1'):
             RECOMMENDATION_COLD_START_TOTAL.labels(endpoint=endpoint, strategy_version=strategy_version).inc()

        return RecommendationResponse(user_id=user_id, recommended_product_ids=recommended_product_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation error: {str(e)}")
    finally:
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(time.time() - start_time)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
