CREATE OR REPLACE VIEW shopping AS
select distinct * from '/home/projects/project-pipeline-distribuited-spark-EKS/process/src/datasets/shopping_amazon_reviews/shopping_amazon_reviews/0.parquet';


select
  rating,
  title,
  text,
  images,
  asin,
  parent_asin,
  user_id,
  timestamp,
  helpful_vote,
  verified_purchase
from shopping limit 100
;


describe
select
  rating,
  title,
  text,
  images,
  asin,
  parent_asin,
  user_id,
  timestamp,
  helpful_vote,
  verified_purchase
from shopping limit 100
;


select mean(rating) from shopping
;

select count(*)-count(distinct concat(user_id, timestamp)) from shopping;




with base as (
    SELECT
        user_id,
        timestamp
    from shopping
    group by user_id, timestamp
    having count(*) > 1
)
select 
  concat(s.user_id, s.timestamp) as concat_user_timestamp,
  s.*
from shopping s
join base b
on s.user_id = b.user_id
and s.timestamp = b.timestamp
order by concat_user_timestamp asc
limit 1000
;
