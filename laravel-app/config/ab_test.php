<?php

return [
    'salt' => env('RECOMMENDATION_AB_TEST_SALT', 'default_ab_test_salt'),

    'experiments' => [
        'default_recommendation_experiment' => [
            'enabled' => true,
            'default_group' => 'control',
            'groups' => [
                'control' => 50,
                'model_v2' => 50,
            ],
        ],
    ],
];
