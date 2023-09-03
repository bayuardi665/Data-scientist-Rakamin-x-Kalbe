select "Marital Status" as marital_status, round(avg(age),3) as avg_age
from customer 
where "Marital Status" != ''
group by marital_status
order by avg_age asc 


select "gender" as avg_gender, round(avg(age),3) as avg_age
from customer c 
group by avg_gender
order by avg_age asc


select st."storename" as store_name, sum (tr.qty) as quantity
from "Transaction" as tr
join store as st
on tr.storeid = st.storeid
group by store_name
order by quantity desc       

select pn."Product Name" as product_name, sum (tr.totalamount)as total_amount
from "product" as pn
join "Transaction" as tr 
on pn.productid = tr.productid
group by product_name
order by total_amount desc 