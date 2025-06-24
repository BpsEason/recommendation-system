<?php

namespace Database\Seeders;

use Illuminate\Database\Console\Seeds\WithoutModelEvents;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class ProductSeeder extends Seeder
{
    /**
     * Run the database seeds.
     */
    public function run(): void
    {
        DB::table('products')->insert([
            [
                'id' => 1,
                'name' => '智慧型手機',
                'description' => '最新款高性能智慧型手機。',
                'price' => 25000.00,
                'category_id' => 'electronics',
                'image_url' => 'https://example.com/phone.jpg',
                'status' => 'active',
                'created_at' => now(), 'updated_at' => now()
            ],
            [
                'id' => 2,
                'name' => '無線藍牙耳機',
                'description' => '音質卓越，佩戴舒適的無線耳機。',
                'price' => 3500.00,
                'category_id' => 'electronics',
                'image_url' => 'https://example.com/earbuds.jpg',
                'status' => 'active',
                'created_at' => now(), 'updated_at' => now()
            ],
            [
                'id' => 3,
                'name' => '筆記型電腦',
                'description' => '輕薄便攜，性能強勁的筆電。',
                'price' => 45000.00,
                'category_id' => 'electronics',
                'image_url' => 'https://example.com/laptop.jpg',
                'status' => 'active',
                'created_at' => now(), 'updated_at' => now()
            ],
            [
                'id' => 4,
                'name' => '智慧手錶',
                'description' => '多功能健康監測智慧手錶。',
                'price' => 8000.00,
                'category_id' => 'wearables',
                'image_url' => 'https://example.com/watch.jpg',
                'status' => 'active',
                'created_at' => now(), 'updated_at' => now()
            ],
            [
                'id' => 5,
                'name' => '行動電源',
                'description' => '大容量快速充電行動電源。',
                'price' => 1200.00,
                'category_id' => 'accessories',
                'image_url' => 'https://example.com/powerbank.jpg',
                'status' => 'active',
                'created_at' => now(), 'updated_at' => now()
            ],
            [
                'id' => 6,
                'name' => '機械式鍵盤',
                'description' => '手感舒適，反應靈敏的機械式鍵盤。',
                'price' => 2800.00,
                'category_id' => 'accessories',
                'image_url' => 'https://example.com/keyboard.jpg',
                'status' => 'active',
                'created_at' => now(), 'updated_at' => now()
            ],
            [
                'id' => 7,
                'name' => '人體工學滑鼠',
                'description' => '專為長時間使用設計的無線滑鼠。',
                'price' => 1500.00,
                'category_id' => 'accessories',
                'image_url' => 'https://example.com/mouse.jpg',
                'status' => 'active',
                'created_at' => now(), 'updated_at' => now()
            ],
            [
                'id' => 8,
                'name' => '高畫質顯示器',
                'description' => '色彩鮮豔，解析度高的電腦顯示器。',
                'price' => 18000.00,
                'category_id' => 'electronics',
                'image_url' => 'https://example.com/monitor.jpg',
                'status' => 'active',
                'created_at' => now(), 'updated_at' => now()
            ],
            [
                'id' => 9,
                'name' => '遊戲主機',
                'description' => '次世代遊戲主機，帶來沉浸式體驗。',
                'price' => 15000.00,
                'category_id' => 'gaming',
                'image_url' => 'https://example.com/console.jpg',
                'status' => 'active',
                'created_at' => now(), 'updated_at' => now()
            ],
            [
                'id' => 10,
                'name' => 'VR 頭戴裝置',
                'description' => '虛擬實境頭戴裝置，開啟新視界。',
                'price' => 30000.00,
                'category_id' => 'gaming',
                'image_url' => 'https://example.com/vr.jpg',
                'status' => 'active',
                'created_at' => now(), 'updated_at' => now()
            ],
            [
                'id' => 11,
                'name' => '咖啡機',
                'description' => '全自動咖啡機，在家享受專業級咖啡。',
                'price' => 5000.00,
                'category_id' => 'home-appliances',
                'image_url' => 'https://example.com/coffee.jpg',
                'status' => 'active',
                'created_at' => now(), 'updated_at' => now()
            ],
            [
                'id' => 12,
                'name' => '空氣清淨機',
                'description' => '高效過濾，改善室內空氣品質。',
                'price' => 7000.00,
                'category_id' => 'home-appliances',
                'image_url' => 'https://example.com/airpurifier.jpg',
                'status' => 'active',
                'created_at' => now(), 'updated_at' => now()
            ],
            [
                'id' => 13,
                'name' => '運動鞋',
                'description' => '輕量緩震跑鞋，適合日常訓練。',
                'price' => 2000.00,
                'category_id' => 'apparel',
                'image_url' => 'https://example.com/shoes.jpg',
                'status' => 'active',
                'created_at' => now(), 'updated_at' => now()
            ],
            [
                'id' => 14,
                'name' => '運動水壺',
                'description' => '耐摔防漏，大容量運動水壺。',
                'price' => 300.00,
                'category_id' => 'sporting-goods',
                'image_url' => 'https://example.com/bottle.jpg',
                'status' => 'active',
                'created_at' => now(), 'updated_at' => now()
            ],
            [
                'id' => 15,
                'name' => '旅遊背包',
                'description' => '多功能旅行背包，大容量設計。',
                'price' => 1800.00,
                'category_id' => 'travel',
                'image_url' => 'https://example.com/backpack.jpg',
                'status' => 'active',
                'created_at' => now(), 'updated_at' => now()
            ],
            [
                'id' => 16,
                'name' => '停售商品 A',
                'description' => '這個商品已經停售了。',
                'price' => 100.00,
                'category_id' => 'misc',
                'image_url' => 'https://example.com/deprecated_a.jpg',
                'status' => 'inactive', # 示範非活躍商品
                'created_at' => now(), 'updated_at' => now()
            ],
            [
                'id' => 17,
                'name' => '已售罄商品 B',
                'description' => '這個商品已經售罄了。',
                'price' => 200.00,
                'category_id' => 'misc',
                'image_url' => 'https://example.com/deprecated_b.jpg',
                'status' => 'sold_out', # 示範售罄商品
                'created_at' => now(), 'updated_at' => now()
            ]
        ]);
    }
}
