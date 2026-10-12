CREATE OR REPLACE VIEW shopping AS
select * from '/home/projects/project-pipeline-distribuited-spark-EKS/process/src/datasets/shopping/shopping/part-00000.parquet';



select * from shopping;



select count(distinct product_id) as product_id from shopping;



SELECT DISTINCT 
    count(*) as  total,
    count(distinct order_id) as order_id,
    count(distinct product_id) as product_id,
    count(distinct seller_id) as seller_id,
    count(distinct customer_unique_id) as customer_unique_id,
    count(distinct product_category_name_english) as product_category_name_english 
FROM shopping
;



SELECT DISTINCT 
    product_category_name_english 
FROM shopping
;



WITH product_ranks AS (
    SELECT
        rank() OVER (ORDER BY product_description_lenght) AS description_length_rank,
        rank() OVER (ORDER BY count(*)) AS purchases_rank
    FROM shopping
    GROUP BY product_id, product_description_lenght
)
SELECT corr(description_length_rank, purchases_rank) AS spearman_correlation
FROM product_ranks;





WITH product_features AS (
    SELECT
        product_id,
        count(*) AS purchases,
        avg(COLUMNS(* EXCLUDE (
            order_id, product_id, seller_id, customer_unique_id,
            seller_state, customer_state, seller_grade,
            product_category_name_english, order_purchase_timestamp
        )))
    FROM shopping
    GROUP BY product_id
),
feature_values AS (
    UNPIVOT product_features
    ON COLUMNS(* EXCLUDE (product_id, purchases))
    INTO NAME feature VALUE feature_value
),
feature_ranks AS (
    SELECT
        feature,
        rank() OVER (PARTITION BY feature ORDER BY feature_value) AS feature_rank,
        rank() OVER (PARTITION BY feature ORDER BY purchases) AS purchases_rank
    FROM feature_values
)
SELECT
    feature,
    round(corr(feature_rank, purchases_rank), 4) AS spearman_correlation
FROM feature_ranks
GROUP BY feature
ORDER BY abs(spearman_correlation) DESC;