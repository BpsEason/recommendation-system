<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('recommendation_events', function (Blueprint $table) {
            $table->id();
            $table->unsignedBigInteger('user_id')->nullable();
            $table->string('experiment_name')->index();
            $table->string('group')->index();
            $table->string('action')->index();
            $table->unsignedBigInteger('product_id')->nullable();
            $table->json('metadata')->nullable();
            $table->timestamps();

            $table->index(['experiment_name', 'group', 'action']);
            $table->index(['user_id', 'created_at']);
        });

        Schema::table('users', function (Blueprint $table) {
            if (!Schema::hasColumn('users', 'recommendation_group')) {
                $table->string('recommendation_group')->nullable()->after('email');
            }
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('recommendation_events');
        Schema::table('users', function (Blueprint $table) {
            if (Schema::hasColumn('users', 'recommendation_group')) {
                $table->dropColumn('recommendation_group');
            }
        });
    }
};
