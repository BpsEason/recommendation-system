import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import os
import pickle
import redis
import random
import time
import mysql.connector
import asyncio # 新增

class Recommender:
    def __init__(self, model_path="model/item_similarity_model.pkl"):
        self.model_path = model_path
        
        try:
            self.redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=int(os.getenv('REDIS_PORT', 6379)), db=0)
            self.redis_client.ping()
            print("Recommender: Successfully connected to Redis.")
        except redis.exceptions.ConnectionError as e:
            print(f"Recommender: Could not connect to Redis: {e}. Model caching might be affected.")
            self.redis_client = None
            
        self.mysql_config = {
            'host': os.getenv('MYSQL_HOST', 'mysql'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'user': os.getenv('MYSQL_USER', 'laravel_user'),
            'password': os.getenv('MYSQL_PASSWORD', 'laravel_password'),
            'database': os.getenv('MYSQL_DB', 'laravel')
        }
        self._mysql_conn = None # 使用單下劃線表示為內部屬性

        # 初始化時加載數據和模型
        self.products = {} # 初始化為空字典
        self.item_similarity_df = pd.DataFrame() # 初始化為空 DataFrame

        # 首次加載
        self.update_product_data()
        self.train_and_save_model() # 首次啟動時訓練或加載模型


    def _get_mysql_connection(self):
        """獲取 MySQL 連接"""
        if self._mysql_conn is None or not self._mysql_conn.is_connected():
            try:
                self._mysql_conn = mysql.connector.connect(**self.mysql_config)
                print("Recommender: Successfully connected to MySQL.")
            except mysql.connector.Error as err:
                print(f"Recommender: Error connecting to MySQL: {err}")
                self._mysql_conn = None
        return self._mysql_conn

    def _load_products_from_mysql(self):
        """
        從 MySQL 資料庫加載產品數據，只獲取 status = 'active' 的商品。
        """
        print("Recommender: Loading active products from MySQL.")
        products_data = {}
        conn = self._get_mysql_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT id, name, category_id, price, image_url, status FROM products WHERE status = 'active'")
                for row in cursor:
                    products_data[row['id']] = {
                        'name': row['name'],
                        'category_id': row['category_id'],
                        'price': float(row['price']), # Ensure price is float
                        'image_url': row['image_url'],
                        'status': row['status']
                    }
                cursor.close()
            except mysql.connector.Error as err:
                print(f"Error fetching products from MySQL: {err}")
            finally:
                if conn.is_connected():
                    conn.close() # 每次查詢後關閉連接
        
        if not products_data:
            print("No active products loaded from MySQL. Falling back to dummy active products for testing.")
            return self._load_dummy_products(active_only=True) # 如果資料庫無數據，仍使用模擬數據
        return products_data

    def _load_user_interactions_from_mysql(self):
        """
        從 MySQL 資料庫加載用戶互動數據 (例如 recommendation_events)。
        """
        print("Recommender: Loading user interactions from MySQL for model training...")
        interactions_data = []
        conn = self._get_mysql_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                # 假設 'action' 為 'click' 或 'purchase' 視為有效互動
                # 您可能需要定義一個 rating_value 映射，例如 click=1, purchase=5
                cursor.execute("""
                    SELECT user_id, product_id, action, COUNT(*) as interaction_count
                    FROM recommendation_events
                    WHERE product_id IS NOT NULL AND user_id IS NOT NULL
                    GROUP BY user_id, product_id, action
                    ORDER BY user_id, product_id, action
                """)
                for row in cursor:
                    # 簡單地將點擊和購買轉化為評分，購買權重更高
                    rating = 1 if row['action'] == 'click' else (5 if row['action'] == 'purchase' else 0)
                    if rating > 0:
                        interactions_data.append({
                            'user_id': row['user_id'],
                            'product_id': row['product_id'],
                            'rating': rating * row['interaction_count'] # 可以根據互動次數加權
                        })
                cursor.close()
            except mysql.connector.Error as err:
                print(f"Error fetching user interactions from MySQL: {err}")
            finally:
                if conn.is_connected():
                    conn.close()
        
        if not interactions_data:
            print("No real user interaction data from MySQL. Using dummy interaction data for training.")
            return self._load_dummy_interactions() # 如果資料庫無數據，仍使用模擬數據
        return pd.DataFrame(interactions_data)

    def _load_dummy_products(self, active_only=False):
        """
        模擬產品數據，包含 category_id 以便測試多樣性。
        新增 active_only 參數來控制是否只返回活躍商品。
        """
        all_products = {
            1: {'name': '智慧型手機', 'price': 25000, 'category_id': 'electronics', 'image_url': 'https://example.com/phone.jpg', 'status': 'active'},
            2: {'name': '無線藍牙耳機', 'price': 3500, 'category_id': 'electronics', 'image_url': 'https://example.com/earbuds.jpg', 'status': 'active'},
            3: {'name': '筆記型電腦', 'price': 45000, 'category_id': 'electronics', 'image_url': 'https://example.com/laptop.jpg', 'status': 'active'},
            4: {'name': '智慧手錶', 'price': 8000, 'category_id': 'wearables', 'image_url': 'https://example.com/watch.jpg', 'status': 'active'},
            5: {'name': '行動電源', 'price': 1200, 'category_id': 'accessories', 'image_url': 'https://example.com/powerbank.jpg', 'status': 'active'},
            6: {'name': '機械式鍵盤', 'price': 2800, 'category_id': 'accessories', 'image_url': 'https://example.com/keyboard.jpg', 'status': 'active'},
            7: {'name': '人體工學滑鼠', 'price': 1500, 'category_id': 'accessories', 'image_url': 'https://example.com/mouse.jpg', 'status': 'active'},
            8: {'name': '高畫質顯示器', 'price': 18000, 'category_id': 'electronics', 'image_url': 'https://example.com/monitor.jpg', 'status': 'active'},
            9: {'name': '遊戲主機', 'price': 15000, 'category_id': 'gaming', 'image_url': 'https://example.com/console.jpg', 'status': 'active'},
            10: {'name': 'VR 頭戴裝置', 'price': 30000, 'category_id': 'gaming', 'image_url': 'https://example.com/vr.jpg', 'status': 'active'},
            11: {'name': '咖啡機', 'price': 5000, 'category_id': 'home-appliances', 'image_url': 'https://example.com/coffee.jpg', 'status': 'active'},
            12: {'name': '空氣清淨機', 'price': 7000, 'category_id': 'home-appliances', 'image_url': 'https://example.com/airpurifier.jpg', 'status': 'active'},
            13: {'name': '運動鞋', 'price': 2000, 'category_id': 'apparel', 'image_url': 'https://example.com/shoes.jpg', 'status': 'active'},
            14: {'name': '運動水壺', 'price': 300, 'category_id': 'sporting-goods', 'image_url': 'https://example.com/bottle.jpg', 'status': 'active'},
            15: {'name': '旅遊背包', 'price': 1800, 'category_id': 'travel', 'image_url': 'https://example.com/backpack.jpg', 'status': 'active'},
            16: {'name': '停售商品 A', 'price': 100, 'category_id': 'misc', 'image_url': 'https://example.com/deprecated_a.jpg', 'status': 'inactive'},
            17: {'name': '已售罄商品 B', 'price': 200, 'category_id': 'misc', 'image_url': 'https://example.com/deprecated_b.jpg', 'status': 'sold_out'}
        }
        if active_only:
            return {pid: info for pid, info in all_products.items() if info['status'] == 'active'}
        return all_products

    def _load_dummy_interactions(self):
        """
        硬編碼的假數據用於訓練。
        """
        dummy_data = {
            'user_id': [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5],
            'product_id': [1, 2, 3, 4, 1, 5, 2, 6, 3, 7, 8, 9, 10, 11, 12, 13, 14, 15, 1, 2],
            'rating': [5, 4, 5, 3, 4, 5, 3, 4, 5, 3, 2, 1, 5, 4, 3, 5, 4, 3, 2, 1]
        }
        return pd.DataFrame(dummy_data)


    # 新增：用於排程器定時調用以更新產品數據
    def update_product_data(self):
        """
        這個方法將被排程器調用，負責：
        1. 從 MySQL 獲取最新的（活躍）產品數據
        2. 更新當前 Recommender 實例中的產品列表
        """
        print("Recommender: Starting product data synchronization...")
        try:
            new_products = self._load_products_from_mysql()
            if new_products:
                self.products = new_products
                print(f"Product data updated successfully. Total active products: {len(self.products)}")
            else:
                print("No new product data to update or MySQL connection failed.")
        except Exception as e:
            print(f"Error during product data update: {e}")

    # 新增：用於排程器定時調用以訓練和保存模型
    def train_and_save_model(self):
        """
        這個方法將會被排程器調用，負責：
        1. 從 MySQL 獲取最新的用戶互動數據
        2. 重新訓練推薦模型
        3. 將新模型保存到文件和 Redis
        4. 熱更新當前 Recommender 實例中的模型
        """
        print("Recommender: Starting model retraining process...")
        try:
            df = self._load_user_interactions_from_mysql()
            if df.empty:
                print("No user interaction data for retraining. Skipping model retraining.")
                return

            # 過濾掉那些不在當前活躍產品列表中的互動數據，確保模型只考慮活躍產品
            active_product_ids = set(self.products.keys())
            df = df[df['product_id'].isin(active_product_ids)]
            
            if df.empty:
                print("No relevant interaction data for active products after filtering. Skipping model retraining.")
                return

            user_product_matrix = df.pivot_table(index='user_id', columns='product_id', values='rating').fillna(0)
            
            # 確保矩陣中至少有兩個產品才進行相似度計算，避免錯誤
            if user_product_matrix.shape[1] < 2:
                print("Not enough unique products in interactions to train similarity model. Skipping.")
                return

            new_item_similarity_df = pd.DataFrame(cosine_similarity(user_product_matrix.T),
                                                  index=user_product_matrix.columns,
                                                  columns=user_product_matrix.columns)
            
            # 保存新模型到文件
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump(new_item_similarity_df, f)
            print(f"Model saved to file: {self.model_path}")

            # 保存新模型到 Redis
            if self.redis_client:
                cache_key = 'item_similarity_model_cache'
                self.redis_client.setex(cache_key, 86400, pickle.dumps(new_item_similarity_df)) # Cache for 1 day
                print("Model saved to Redis cache.")
            else:
                print("Redis client not available, skipping model caching to Redis.")
            
            # 熱更新當前實例的模型
            self.item_similarity_df = new_item_similarity_df
            print("Model retraining and hot-swapping completed successfully.")
        except Exception as e:
            print(f"Error during model retraining: {e}")
            import traceback
            traceback.print_exc() # 打印完整的錯誤堆棧

    def _get_user_recent_views(self, user_id: int):
        """
        從 MySQL 或 Redis 獲取用戶最近的瀏覽產品。
        這裡為了示例仍用隨機數據，但會過濾掉非活躍產品。
        """
        print(f"Fetching recent views for user {user_id} (placeholder).")
        
        active_product_ids = list(self.products.keys())
        if not active_product_ids:
            return [] # 如果沒有活躍產品，則沒有最近瀏覽

        random.seed(user_id + int(time.time() / 3600))
        # 確保只從活躍產品中選擇
        viewed_products = random.sample(active_product_ids, k=min(len(active_product_ids), random.randint(2, 5)))
        return viewed_products

    def get_recommendations(self, user_id: int, strategy_version: str = 'v1', num_recommendations: int = 10) -> list[int]:
        """
        根據用戶 ID 和策略版本獲取推薦產品 ID 列表。
        會過濾掉非活躍商品。
        """
        print(f"Generating recommendations for user {user_id} using strategy {strategy_version}")

        viewed_products = self._get_user_recent_views(user_id)
        print(f"User {user_id} viewed products: {viewed_products}")

        all_active_product_ids = list(self.products.keys())
        if not all_active_product_ids:
            print("No active products available in catalog. Returning empty recommendations.")
            return []

        generated_recommendations = []

        if strategy_version == 'v1':
            if viewed_products and not self.item_similarity_df.empty:
                available_viewed_products = [p for p in viewed_products if p in self.item_similarity_df.columns and p in self.products and self.products[p]['status'] == 'active']
                
                if available_viewed_products:
                    seen_products_df = self.item_similarity_df[available_viewed_products]
                    sum_similarities = seen_products_df.sum(axis=1)

                    # 篩選掉非活躍產品和已看過的產品
                    candidate_recommendations = sum_similarities.drop(viewed_products, errors='ignore').sort_values(ascending=False).index.tolist()
                    
                    for pid in candidate_recommendations:
                        if pid in self.products and self.products[pid]['status'] == 'active':
                            generated_recommendations.append(pid)
                        if len(generated_recommendations) >= num_recommendations:
                            break
                
            if len(generated_recommendations) < num_recommendations:
                # 從所有活躍產品中隨機補充
                remaining_active_products = [p for p in all_active_product_ids if p not in generated_recommendations and p not in viewed_products]
                random.shuffle(remaining_active_products)
                generated_recommendations.extend(remaining_active_products[:num_recommendations - len(generated_recommendations)])
                
        elif strategy_version == 'v2':
            print(f"Applying v2 strategy for user {user_id} (more diverse recommendation).")
            base_recommendations = []
            if viewed_products and not self.item_similarity_df.empty:
                available_viewed_products = [p for p in viewed_products if p in self.item_similarity_df.columns and p in self.products and self.products[p]['status'] == 'active']
                if available_viewed_products:
                    seen_products_df = self.item_similarity_df[available_viewed_products]
                    sum_similarities = seen_products_df.sum(axis=1)
                    # 先生成所有可能的相似推薦，稍後再過濾活躍和未看過
                    base_candidate_pids = sum_similarities.drop(viewed_products, errors='ignore').sort_values(ascending=False).index.tolist()
                    for pid in base_candidate_pids:
                        if pid in self.products and self.products[pid]['status'] == 'active':
                            base_recommendations.append(pid)
                        if len(base_recommendations) >= num_recommendations * 2: # 獲取多一點作為基礎
                            break

            diverse_products = []
            shuffled_active_product_ids = all_active_product_ids[:]
            random.shuffle(shuffled_active_product_ids)

            selected_categories = set()
            for pid in shuffled_active_product_ids:
                if pid not in viewed_products and pid not in base_recommendations: # 確保不重複
                    product_info = self.products.get(pid)
                    if product_info and product_info['status'] == 'active':
                        category = product_info.get('category_id')
                        if category and category not in selected_categories:
                            diverse_products.append(pid)
                            selected_categories.add(category)
                            if len(diverse_products) >= num_recommendations // 2:
                                break
            
            # 合併基礎推薦和多樣性推薦，並確保唯一性
            combined_recommendations = list(set(base_recommendations[:num_recommendations // 2] + diverse_products))
            random.shuffle(combined_recommendations)

            # 最終填充到足夠數量 (從所有活躍產品中隨機補充)
            if len(combined_recommendations) < num_recommendations:
                remaining_active_products = [p for p in all_active_product_ids if p not in combined_recommendations and p not in viewed_products]
                random.shuffle(remaining_active_products)
                combined_recommendations.extend(remaining_active_products[:num_recommendations - len(combined_recommendations)])
            
            generated_recommendations = combined_recommendations

        else:
            print(f"Unknown strategy version: {strategy_version}. Falling back to random active items.")
            random.shuffle(all_active_product_ids)
            generated_recommendations = all_active_product_ids

        return generated_recommendations[:num_recommendations]

