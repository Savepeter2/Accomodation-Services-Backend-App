This is an API for an Accommodation Service App. 

**How it works:**

1.	The app is divided into two parts: The Explorer page and the Accommodation Provider page.
2.	Users register on the app as either an explorer or accommodation provider.
3.	Accommodation providers complete their required profile details, then proceed to create listings. Listings are available accommodations posted by the accommodation provider and include all details about the accommodation (e.g., location, room pictures, kitchen, price, etc.). Each accommodation provider can create as many listings as they want.
4.	Explorers, whose objective is to search for available listings, go to the Explorer page and view all the available listings posted by the accommodation providers.
5.	Explorers can filter listings by type (e.g., motel, serviced apartment, flat, etc.).
6.	When an explorer decides to get more information on a suitable listing, the accommodation provider that posted the listing displays the listing details to the explorer, who can then easily contact them.

**Requirements:**

1.	Users should be able to sign up and verify their email before logging in.
2.	Users should provide their first name, last name, email, and password when signing up and use their email and password to sign in.
3.	A verification email is sent to the user's email upon sign up, which expires after 30 minutes. Users can resend a verification email.
4.	Users can reset their password if forgotten by providing the email used during sign up. They receive a password reset token via email, which expires after 5 minutes. They provide this token along with their new password to reset their password.
5.	Users can log in with their username (email) and password.
6.	Users can log out from the app.
7.	Users can sign up as either an explorer or an accommodation provider.
8.	Accommodation providers should be able to view their profile, including their dashboard, which displays their number of listings, likes, reviews, and profile visits. They should also be able to view a trend chart of their profile visits.
9.	Accommodation providers should be able to create, update, view all their listings, and delete listings.
10.	accommodation type (e.g., hotel, hostel, serviced apartment, etc.).
11.	Explorers should be able to view an accommodation provider's profile from the listing.
12.	Explorers should be able to like a listing and add a review to a listing.
13.	When an explorer views a particular listing posted by an accommodation provider, and the explorer likes the listing, the total number of likes the accommodation provider has increases. When the explorer views the profile, the provider's total number of profile visits increases. When the explorer adds a review, the total number of reviews also increases.


# Accommodation Service API Documentation

## User

### SignUp

**POST** /user/signup

This endpoint creates a new user.

**Request:**

```bash
curl --location 'https://accom-services-app.onrender.com/user/signup' \
--data-raw '{
  "first_name": "Peter",
  "last_name": "Adekolu",
  "email": "saveadekolu@gmail.com",
  "profile": "Accommodation Provider",
  "password": "Antivirus.1",
  "confirm_password": "Antivirus.1"
}'
```

**Response:**

```json
{
    "status": "success",
    "message": "User created successfully",
    ...
}
```

### Verify Email

**GET** /user/confirm-email/{token}

This endpoint verifies the user's email.

**Request:**

```bash
curl --location 'https://accom-services-app.onrender.com/user/confirm-email/{token}'
```

**Response:**

```json
{
    "detail": {
        "status": "error",
        "message": "Token Expired, please resend verification mail",
        ...
    }
}
```

### Resend Verification Link

**GET** /user/resend-verification-email?email={email}

This endpoint resends the verification email.

**Request:**

```bash
curl --location 'https://accom-services-app.onrender.com/user/resend-verification-email?email=saveadekolu%40gmail.com'
```

**Response:**

```json
{
    "status": "success",
    "message": "Mail for Email verification has been sent successfully",
    ...
}
```

### Forgot Password

**GET** /user/forgot-password?email={email}

This endpoint sends a password reset email.

**Request:**

```bash
curl --location --request POST 'https://accom-services-app.onrender.com/user/forgot-password?email=saveadekolu%40gmail.com'
```

**Response:**

```json
{
    "status": "success",
    "message": "Mail for password reset has been sent successfully",
    ...
}
```

### Reset Password

**GET** /user/reset-password/?new_password={new_password}&confirm_password={confirm_password}&password_reset_token={token}

This endpoint resets the user's password.

**Request:**

```bash
curl --location 'https://accom-services-app.onrender.com/user/reset-password/?new_password=Antivirus.123&confirm_password=Antivirus.123&password_reset_token={token}' \
--data-raw '{
  "email": "saveadekolu@gmail.com"
}'
```

**Response:**

```json
{
    "status": "success",
    "message": "Password changed successfully",
    ...
}
```

### Login

**GET** /user/login

This endpoint logs in the user.

**Request:**

```bash
curl --location 'https://accom-services-app.onrender.com/user/login' \
--data-urlencode 'username=saveadekolu@gmail.com' \
--data-urlencode 'password=Antivirus.123'
```

**Response:**

```json
{
    "status": "success",
    "message": "User has been logged in successfully",
    ...
}
```

### Profile Information

**GET** /user/me

This endpoint retrieves the user's profile information.

**Request:**

```bash
curl --location 'https://accom-services-app.onrender.com/user/me'
```

**Response:**

```json
{
    "status": "success",
    "message": "User retrieved successfully",
    ...
}
```

### Update User Profile

**PATCH** /user/me/profile/update

This endpoint updates the user's profile.

**Request:**

```bash
curl --location --request PATCH 'https://accom-services-app.onrender.com/user/me/profile/update' \
--form 'first_name="pet"' \
--form 'last_name="explorer_lastname"' \
--form 'profile_picture=@"4TBlo-B8o/Company DB.png"'
```

**Response:**

```json
{
    "status": "success",
    "message": "User profile updated successfully",
    ...
}
```

### Logout

**POST** /user/logout

This endpoint logs out the user.

**Request:**

```bash
curl --location --request POST 'https://accom-services-app.onrender.com/user/logout'
```

**Response:**

```json
{
    "status": "success",
    "message": "User has been logged out successfully",
    ...
}
```

To integrate the Accommodation Provider endpoints into your GitHub README, you can follow a similar structured format. Here's how you can present it:

---

# Accommodation Provider Endpoints

## Create Accommodation Provider Profile

**GET** /accomodation_provider/create

Creates a new Accommodation Provider profile.

**Request:**

```bash
curl --location 'https://accom-services-app.onrender.com/accomodation_provider/create' \
--data '{
  "brand_name": "rolling gadgets",
  "phone_num": "08068168282",
  "brand_address": "computer village",
  "state": "OSUN",
  "city": "Osogbo"
}'
```

**Response:**

```json
{
    "detail": {
        "status": "error",
        "message": "Accommodation Provider profile already exists",
        "body": ""
    }
}
```

## Get Accommodation Provider Profile

**GET** /accomodation_provider/profile/me

Retrieves the current Accommodation Provider's profile.

**Request:**

```bash
curl --location 'https://accom-services-app.onrender.com/accomodation_provider/profile/me'
```

**Response:**

```json
{
    "status": "success",
    "message": "Accommodation Provider profile retrieved successfully",
    ...
}
```

## Update Accommodation Provider Profile

**GET** /accomodation_provider/profile/me/update

Updates the current Accommodation Provider's profile.

**Request:**

```bash
curl --location --request PATCH 'https://accom-services-app.onrender.com/accomodation_provider/profile/me/update' \
--form 'brand_name="ROLLING ROLLING"' \
--form 'phone_number="08028276338"' \
--form 'brand_address="Richland Hostel"' \
--form 'state="OSUN"' \
--form 'city="osogbo"' \
--form 'profile_picture=@"MkMLXlk0Y/blockchain technology.png"'
```

**Response:**

```json
{
    "status": "success",
    "message": "Accommodation Provider profile updated successfully",
    ...
}
```

## Accommodation Provider Dashboard

**GET** /accomodation_provider/home

Retrieves Accommodation Provider dashboard information.

**Request:**

```bash
curl --location 'https://accom-services-app.onrender.com/accomodation_provider/home'
```

**Response:**

```json
{
    "status": "success",
    "message": "Accommodation Provider dashboard retrieved successfully",
    ...
}
```

# Listings Endpoints

This section outlines the endpoints related to managing listings within the Accommodation Service API.

## Create a Listing

**POST** /accomodation_provider/listing/create

Creates a new accommodation listing.

**Request:**

```bash
curl --location 'https://accom-services-app.onrender.com/accomodation_provider/listing/create' \
--form 'accomodation_name="hotel suite"' \
--form 'description="a good suite"' \
--form 'accomodation_address=" oduduwa estate"' \
--form 'accomodation_type="HOSTEL"' \
--form 'number_of_rooms="12"' \
--form 'number_of_kitchen="12"' \
--form 'number_of_bathrooms="2"' \
--form 'state="LAGOS"' \
--form 'city="lekki"' \
--form 'accom_images=@"1XCMsW9c7/blockchain technology.png"'
```

**Response:**

```json
{
    "status": "success",
    "message": "Accommodation Provider listing created successfully",
    ...
}
```

## Get a Listing

**GET** /accomodation_provider/listing/filter/3?listing_id=3

Retrieves details of a specific listing.

**Request:**

```bash
curl --location 'https://accom-services-app.onrender.com/accomodation_provider/listing/filter/3?listing_id=3'
```

**Response:**

```json
{
    "status": "success",
    "message": "Listing retrieved successfully",
    ...
}
```

## Get All Listings

**GET** /accomodation_provider/listings/filter

Retrieves all available listings.

**Request:**

```bash
curl --location 'https://accom-services-app.onrender.com/accomodation_provider/listings/filter'
```

**Response:**

```json
{
    "status": "success",
    "message": "Listings retrieved successfully",
    ...
}
```

## Update Listing

**PATCH** /accomodation_provider/listing/update/1?listing_id=1

Updates details of a specific listing.

**Request:**

```bash
curl --location --request PATCH 'https://accom-services-app.onrender.com/accomodation_provider/listing/update/1?listing_id=1' \
--form 'accomodation_name="first_listing"' \
--form 'description="a good one"' \
--form 'accomodation_address="oduduwa esatet"' \
--form 'accomodation_type="HOSTEL"' \
--form 'number_of_rooms="12"' \
--form 'number_of_kitchen="10"' \
--form 'number_of_bathrooms="5"' \
--form 'state="OSUN"' \
--form 'city="osogbo"' \
--form 'accom_images=@"6ShwY_W5i/Company DB.png"'
```

**Response:**

```json
{
    "status": "success",
    "message": "Listing updated successfully",
    ...
}
```

## Delete Listing

**DELETE** /accomodation_provider/listing/delete/1?listing_id=1

Deletes a specific listing.

**Request:**

```bash
curl --location --request DELETE 'https://accom-services-app.onrender.com/accomodation_provider/listing/delete/1?listing_id=1'
```

**Response:**

```json
{
    "status": "success",
    "message": "Listing deleted successfully",
    ...
}
```
To organize the Explorer section for your GitHub README, you can structure it as follows:

---

# Explorer Endpoints

This section details the endpoints related to exploring and interacting with accommodation listings within the Accommodation Service API.

## Explore all Listings

**POST** /explorer/explore/accomodation_listings

Retrieves all available accommodation listings.

**Request:**

```bash
curl --location --request POST 'https://accom-services-app.onrender.com/explorer/explore/accomodation_listings'
```

**Response:**

```json
[
    {
        "accomodation_type": "MOTEL",
        "accomodation_state": "LAGOS",
        "number_of_rooms": 14,
        "no_likes": 1,
        "accomodation_name": "iphone 16 office",
        "id": 2,
        "accomodation_city": "Yaba"
    },
    {
        "accomodation_type": "HOSTEL",
        "accomodation_state": "LAGOS",
        "number_of_rooms": 12,
        "no_likes": 0,
        "accomodation_name": "hotel suite",
        "id": 3,
        "accomodation_city": "Lekki"
    }
]
```

## Filter Listings

**POST** /explorer/explore/accomodation_listings/filter/HOSTEL?acc_type=HOSTEL

Filters accommodation listings by type.

**Request:**

```bash
curl --location --request POST 'https://accom-services-app.onrender.com/explorer/explore/accomodation_listings/filter/HOSTEL?acc_type=HOSTEL'
```

**Response:**

```json
[
    {
        "accomodation_type": "HOSTEL",
        "accomodation_state": "LAGOS",
        "number_of_rooms": 12,
        "no_likes": 0,
        "accomodation_name": "hotel suite",
        "id": 3,
        "accomodation_city": "Lekki"
    }
]
```

## Explore Listing Details

**POST** /explorer/explore/accomodation_listings/2?accomodation_listing_id=2

Retrieves details of a specific accommodation listing.

**Request:**

```bash
curl --location --request POST 'https://accom-services-app.onrender.com/explorer/explore/accomodation_listings/2?accomodation_listing_id=2'
```

**Response:**

```json
{
    "status": "success",
    "message": "Listing details retrieved",
    "body": {
        "listing_details": {
            ...
        }
    }
}
```

## Explore Listing Agent Details

**POST** /explorer/explore/accomodation_listings/2/agent_details?accomodation_listing_id=2

Retrieves details of the agent associated with a specific accommodation listing.

**Request:**

```bash
curl --location --request POST 'https://accom-services-app.onrender.com/explorer/explore/accomodation_listings/2/agent_details?accomodation_listing_id=2'
```

**Response:**

```json
{
    "status": "success",
    "message": "Listing details retrieved",
    "body": {
        "listing_details": {
            ...
        },
        "agent_details": {
            ...
        }
    }
}
```

## Like Listing

**POST** /explorer/explore/accomodation_listings/2/like?accomodation_listing_id=2

Likes a specific accommodation listing.

**Request:**

```bash
curl --location --request POST 'https://accom-services-app.onrender.com/explorer/explore/accomodation_listings/2/like?accomodation_listing_id=2'
```

**Response:**

```json
{
    "detail": {
        "status": "error",
        "message": "Listing already liked",
        "body": ""
    }
}
```

## Add Review

**POST** /explorer/explore/accomodation_listings/2/add_review?accomodation_listing_id=2

Adds a review to a specific accommodation listing.

**Request:**

```bash
curl --location 'https://accom-services-app.onrender.com/explorer/explore/accomodation_listings/2/add_review?accomodation_listing_id=2' \
--data-urlencode 'review=a good one'
```

**Response:**

```json
{
    "status": "success",
    "message": "Review added",
    "body": {
        ...
    }
}
```


