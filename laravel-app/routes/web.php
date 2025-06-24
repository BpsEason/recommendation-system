<?php

use Illuminate\Support\Facades\Route;
use Illuminate\Support\Facades\Auth;
use App\Models\User;

/*
|--------------------------------------------------------------------------
| Web Routes
|--------------------------------------------------------------------------
|
| Here is where you can register web routes for your application. These
| routes are loaded by the RouteServiceProvider and all of them will
| be assigned to the "web" middleware group. Make something great!
|
*/

Route::get('/', function () {
    return 'Welcome to the Recommendation System! Try /login-test/1 then /api/user/recommendations. Also check /products for dummy product list.';
});

Route::get('/login-test/{id}', function ($id) {
    $user = User::find($id);
    if (!$user) {
        $user = User::factory()->create([
            'id' => $id, 
            'name' => "Test User {$id}", 
            'email' => "test{$id}@example.com",
            'password' => bcrypt('password'),
        ]); 
    }
    Auth::login($user);
    session()->regenerate();
    return "Logged in as User ID: " . $user->id . ". Visit /api/user/recommendations";
});

Route::get('/logout', function () {
    Auth::logout();
    request()->session()->invalidate();
    request()->session()->regenerateToken();
    return "Logged out.";
});

// 簡易產品列表，用於驗證上下架狀態
Route::get('/products', function() {
    $products = \App\Models\Product::all();
    return view('products_list', ['products' => $products]);
});
