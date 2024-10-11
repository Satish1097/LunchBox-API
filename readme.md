                                      Lunch Box API
 
Login/Signup
1. Send OTP:-

For generating random OTP we are using ‘Pyotp’ library that generates a secret key then creates OTP. I am using Time Based OTP.  After generating OTP we can set the lifespan of that OTP.
We are creating OTP table for storing the secret key that we are using in OTP verification.
OTP table has a flag “Is_used” that indicates the OTP is used or not.
For sending OTP to Mobile Number We’re using Twilio for free.


2.  Verify OTP:-

To verify OTP we are using stored secret key in OTP table and verify that with the help of Pyotp library.
After successfully Verification of OTP We are changing the flag of is_verified=True that is by default False.
After verification we are creating user that have only mobile number initially
There are Two Flag in User Table that will help in User Registration:-
1. is_verified
2. is_profile_completed
Token is created after Verification and return in response.


3. Personal Detail:-

User is already created in verify OTP API so in personal detail We are just updating the user instance to add more information.
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
ii)      List Rating:- No Authentication required to list rating, any one can see the ratings of a particular item.


8. Menu Item:-

There are 5 API’s for the MenuItem:-
i)                Add MenuItem:- Only Admin User Can Add MenuItem
ii)              ListMenuItem:-Authenticated can see the MenuItems
iii)             Retrieve MenuItem:-User can see the particular MenuItem
iv)             Update MenuItem:-Only AdminUser can Update the MenuItem
v)              Delete MenuItem:- Only AdminUser can Delete the MenuItem
 

9. Cart:-

There are 6 Api for Cart:-
AddtoCart:-Parent can add item in cart for particular child with quantity.
View Cart:- Authenticated User Can View the cart with menu_item, quantity, unit price,subtotal and cart_total.
View with child:-User can see the particular child cart.
User can see the detail of the menu_item in cart
Update Cart Item frequency
Delete Cart Item


10. Order:-

Create Order:- User can create order for his/her child Order is created based on the items in cart. After creating order cart items will be vanished.

View Order: user can see the order of his/her child.

Update Order:-In Update Order user can can cancel the order and admin can change the status of the order.

Retrive Order:-Using this API we can retrieve a particular Order


11. Plan:-

Create Plan: only admin User can create/add plan.

View plan: Only authenticated User can view the plan.

Retrieve Plan: Only Authenticated User can retrieve the plan.

Update Plan: Only Admin User can Update the plan.

Delete: Only Admin User can delete the plan.

12.Subscription:-


