Lunch Box API
 
Login/Signup
1. Send OTP:-
For generating random OTP we are using the ‘Pyotp’ library that generates a secret key then creates OTP. I am using Time Based OTP.  After generating OTP we can set the lifespan of that OTP.
We are creating an OTP table for storing the secret key that we are using in OTP verification.
The OTP table has a flag “Is_used” that indicates whether the OTP is used or not.
For sending OTP to Mobile Number We’re using Twilio for free.

2.  Verify OTP:-
To verify OTP we are using a stored secret key in OTP table and verify that with the help of Pyotp library.
After successfully Verification of OTP We are changing the flag of is_verified=True that is by default False.
After verification we are creating user that have only mobile number initially
There are Two Flag in User Table that will help in User Registration:-
1. is_verified
2. is_profile_completed
Token is created after Verification and returned in response.

3. Personal Detail:-
User is already created to verify OTP API so in personal detail We are just updating the user instance to add more information.
After adding personal detail we’re update the flag is_profile_completed=True
4. Child:-
There are 4 API’s for Child:-

i)                Add Child
ii)             Update Child-Only parent of the child can update the child details
iii)             Retrieve Child – Parent can See the Child Associated with them
iv)             Delete Child- only Parent of the children can delete the record of child
5. Cuisine:-
There are 3 API’s for Cuisine:-

i)                Add Cuisine:-Only Admin can Add Cuisine
ii)              List Cuisine:-Any one can list the Cuisine
iii)             Delete Cuisine:- Only Admin Can delete Cuisine

6. Check User Status:-

There is an Api to check the User Registration and Verification Status, User Completed their profile or not and then proceed further.

7. Rating
There are two API’s for Rating
i)        Add Rating:- only Authenticated user can add rating on any product at once, single user can not rate a products multiple times rating in 1-5, min value=1 and max value=5
ii)      List Rating:- No Authentication required to list rating, anyone can see the ratings of a particular item.
8. Menu Item:-
There are 5 API’s for the MenuItem:-
i)                Add MenuItem:- Only Admin User Can Add MenuItem
ii)              ListMenuItem:-Authenticated can see the MenuItems
iii)             Retrieve MenuItem:-User can see the particular MenuItem
iv)             Update MenuItem:-Only AdminUser can Update the MenuItem
v)              Delete MenuItem:- Only AdminUser can Delete the MenuItem
 
9. Cart:-

There are 6 Api for Cart:-

AddtoCart:-Parent can add items in cart for particular child with quantity.

View Cart:- Authenticated User Can View the cart with menu_item, quantity, unit price,subtotal and cart_total.

View with child:-User can see the particular child cart.

User can see the detail of the menu_item in cart

Update Cart Item frequency

Delete Cart Item


10. Order:-

Create Order:- User can create order for his/her child Order is created based on the items in cart. After creating order cart items will be vanished.

View Order: user can see the order of his/her child.

Update Order:-In Update Order user can cancel the order and admin can change the status of the order.

Retrieve Order:-Using this API we can retrieve a particular Order
11. Plan:-

Create Plan: only admin users can create/add plans.

View plan: Only authenticated users can view the plan.

Retrieve Plan: Only Authenticated Users can retrieve the plan.

Update Plan: Only Admin Users can Update the plan.

Delete: Only Admin User can delete the plan.



12.Subscription:-

Create Subscription:- Only Parent can create subscription for the child

Get Subscription:-Parent can see the Subscription for selected child

There are two console command created to manage subscription:-

Create Order:- In this console command every day an order is created for the child in subscription list

Check_Subscription:- In this console command we will check the subscription date and update the date if any order is cancelled for the day and if all order of subscription is completed then we will expire the subscription.

To execute both commands  we will use the task scheduler that runs the both commands everyday at specific times.

13.Payment API:-

Pay:-It creates the razorpay payment order to pay.

paymentHandler:- It verifies the signature and captures the payment after payment and updates the payment status in the TransactionDetail table.
    
14.Transaction:- 
View Transaction:-User can see the transaction Detail for selected child

