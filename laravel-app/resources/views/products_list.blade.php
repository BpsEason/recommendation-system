<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Product List</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .product { border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; }
        .product.inactive { background-color: #fdd; }
        .product.sold_out { background-color: #ffd; }
        .status-active { color: green; font-weight: bold; }
        .status-inactive { color: red; }
        .status-sold_out { color: orange; }
    </style>
</head>
<body>
    <h1>Product List</h1>
    <p>This page shows all products, including inactive and sold out ones, to help verify the recommender's filtering.</p>
    <p>Only <span class="status-active">active</span> products should appear in recommendations.</p>
    <div>
        @foreach($products as $product)
            <div class="product {{ $product->status }}">
                <h3>{{ $product->name }} (ID: {{ $product->id }})</h3>
                <p><strong>Price:</strong> ${{ number_format($product->price, 2) }}</p>
                <p><strong>Category:</strong> {{ $product->category_id }}</p>
                <p><strong>Status:</strong> <span class="status-{{ $product->status }}">{{ $product->status }}</span></p>
                @if($product->image_url)
                    <img src="{{ $product->image_url }}" alt="{{ $product->name }}" width="100">
                @endif
                <p>{{ $product->description }}</p>
            </div>
        @endforeach
    </div>
</body>
</html>
