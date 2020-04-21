## **Project Description:**

As part of this mini project I have designed a simple **Online Book Shopping application** to demonstrate the use of REST APIs. The application is designed using Flask Python web framework and uses Cassandra Cloud Database. The following Usecases are considered.

 - **Home Page**
	 - This is the landing page of the application
	 - It used GET requests to retrieve User, Product and Category information from the Cassandra database
	 - Home page also has details fetched from external APIs to display Current City Weather and Current Exchange rates
	 - API Endpoint Path: **/**
	 
 - **Add Item Page**	
	 - This page is used by ‘admin’ user to add new products using POST
	   request.	 
	 - API Endpoint Path: **/addItem**
	 
 - **Remove Item Page**
	 - This page is used by ‘admin’ users to remove products using DELETE request
	 - API Endpoint Path: **/removeItem/<product_ID>**
 - **Update Product Stock Count**
	 - This is to update the stock count of the given product id
	 - API Endpoint Path: **/updateStockCount/<product_ID>/\<stockCount>**

## **Setting up the Application in AWS**

1. Login to AWS Educate platform

2. Start an EC2 instance and log into it

3. Download and unzip the Git repository folders to the EC2 ubuntu instance to a new folder ‘MiniProject’

4. Install docker using the following commands:

	**sudo apt update**

	**sudo apt install docker.io**

5. Build the docker image of our application using the below command

	**sudo docker build . --tag=ebookshop_app_image:v1**

6. Verify if the required docker image is built using,

	**sudo docker images**

7. Once the docker image is built successfully, we need to setup and start the Cassandra database

	**sudo docker pull cassandra:latest**

	**sudo docker run --name cassandra_ebookstore -p 9042:9042 -d cassandra:latest**

8. Verify if the Cassandra docker instance is running using the command

	**sudo docker ps**

9. Now run the docker image of our application, which will run the required application:

	**sudo docker run -p 443:443 ebookshop_app_image:v1**

10. Open the public AWS DNS address or IP address and the application should be running

## **Cassandra Database Initialization:**

The Cassandra cloud database is populated using the application script (ebookshop.py). The initialization script runs before every first request to the application, implemented using the Flask tag **@app.before_first_request**. It will populate the data for 'Users', 'Categories' and 'Products' tables.

## **External APIs used:**

There are **three external APIs** used to complement the functionality of the application.

 - **ipinfo** - IP geolocation API to get the current location of the IP address          
 - **openweathermap** - To get the current weather data for the current location detected. This information is displayed in the home
        page        
 -  **openexchangerates** – To get the live exchange rates for GBP to USD and EUR. Again, this information is displayed in the home
        page
<![endif]-->

## **Cloud Security Measures:**

**1.** **Application Security:**

 - **Basic HTTP authentication** has been implemented to authenticate every request to the API endpoints. It is achieved using
   **Flask-HTTPAuth** extension and **@auth.login_required** tag

**2.** **Application Over HTTPS:**

 - To serve the application over HTTPS, I have used **Self-Signed      
   Certificates** which uses private key(**‘key.pem'**) and certificate(**‘cert.pem’**) placed in the root directory
 - **pyOpenSSL** python package is used for the implementation and application is accessed over SSL context on port **443**

**3.** **Database Roles:**
 - Every user is assigned a role. Currently the application has **two
   roles ‘admin’ and ‘user’**
 - Only the user with the specified role can perform database
   operations. This is implemented inside the API endpoints. Eg. addItem
   can be performed only by ‘admin.

## **Kubernetes Load Balancing**

1. I have used MicroK8s which is an upstream Kubernetes deployment that runs entirely on the local workstation. Install it using the command inside AWS EC2 instance:
	**sudo snap install microk8s -classic**

2. Enable registry with the following command:
	**sudo microk8s enable registry**

3. To upload images to MicroK8s, we have to tag them with localhost:32000/image-name before pushing them:
	**sudo docker tag 4e7eeee3e994 localhost:32000/ebookshop_app_image:registry**

4. Now that the image is tagged, it can be pushed to the registry:
	**sudo docker push localhost:32000/ebookshop_app_image**

5. Edit **/etc/docker/daemon.json** and add:
	**{**
	**"insecure-registries" : ["localhost:32000"]**
	**}**

6. The new configuration should be loaded with a Docker daemon restart:
	**sudo systemctl restart docker**

7. Deploy docker container image present in the registry using the command:
	**sudo microk8s.kubectl apply -f ./deployment.yaml**

8. View deployment status
	**sudo microk8s.kubectl get deployment**
	
9. View the created kubernetes pods
	**sudo microk8s.kubectl get pods**

10. Create a service and expose the deployment to internet
	**sudo microk8s.kubectl expose deployment ebookshop-deployment --port=443 --type=LoadBalancer**
	**sudo microk8s.kubectl get services**


## **API Endpoints:**

Once the application is running on the public DNS address, we are ready to send the requests to the API endpoints we have developed. This can be done using **curl commands** or through application web pages using **browser**. I will describe endpoint requests and the possible responses using the curl commands.

## **GET:**

## **Path:** /

**Request:**

curl -i -H "Content-Type: application/json" -u annaheckel:mypassword https://ec2-54-204-128-236.compute-1.amazonaws.com --cacert cert.pem -k

**Response:**

HTTP/1.0 200 OK
Content-Type: application/json
Content-Length: 1531
Server: Werkzeug/1.0.1 Python/3.7.7
Date: Mon, 20 Apr 2020 19:34:24 GMT

{
  "GBP-EUR": 1.15,
  "GBP-USD": 1.24,
  "categories": [
    [
      5,
      "Computer Programming"
    ],
    [
      1,
      "Personal Growth"
    ],
    [
      2,
      "Autobiographies"
    ],
    [
      4,
      "Fiction"
    ],
    [
      3,
      "Political Science"
    ]
  ],
  "products": [
    [
      1,
      "How to win friends & influence people",
      95,
      "If you are about to enter the corperate world , you have to read this !",
      "HowToWinFriends.jpg",
      29
    ],
    [
      2,
      "Seeing like a state",
      300,
      "James Scott analyses how certain schemes to improve the human condition ahve failed",
      "SeeingLikeAState.jpg",
      3
    ],
    [
      4,
      "MasteringCloudComputing",
      70,
      "MasteringCloudComputing",
      "MasteringCloudComputing.jpg",
      20
    ],
    [
      770126,
      "test",
      25,
      "fdsf",
      "ml.jpeg",
      3
    ],
    [
      364291,
      "MachineLearningAnAlgorithmicPerspective",
      50,
      "Predictive Analytics with Microsoft Azure Machine Learning, Second Edition",
      "MachineLearningAnAlgorithmicPerspective.jpg",
      3
    ],
    [
      3,
      "Big Data Processing Using Spark in Cloud",
      100,
      "Big Data Processing Using Spark in Cloud",
      "BigDataProcessingUsingSparkInCloud.jpg",
      10
    ]
  ],
  "weather": {
    "city": "Virginia Beach",
    "description": "moderate rain",
    "temperature": 12.04
  }
}

-------------------------------------------------------------------------------------------------------

## **POST:**


## Path: /addItem


**Request:**

HTTP/1.0 201 CREATED
Content-Type: application/json
Content-Length: 291
Vary: Cookie
Set-Cookie: session=eyJfZmxhc2hlcyI6W3siIHQiOlsibWVzc2FnZSIsIlByb2R1Y3QgYWRkZWQgc3VjY2Vzc2Z1bGx5ISJdfV19.Xp33Og.7-TtwbLicG-op7ZTrsYXjqAv5qs; HttpOnly; Path=/
Server: Werkzeug/1.0.1 Python/3.7.7
Date: Mon, 20 Apr 2020 19:25:46 GMT

{

"category": "5",

"description": "Predictive Analytics with Microsoft Azure Machine Learning, Second Edition",

"image": "MachineLearningAnAlgorithmicPerspective.jpg",

"name": "MachineLearningAnAlgorithmicPerspective",

"price": "50",

"product_id": 364291,

"stock": "3"

}

-------------------------------------------------------------------------------------------------------

**Request:**

curl -i -X POST -H "Content-Type: multipart/form-data" -F 'image=@/home/ubuntu/MiniProject/static/images/MachineLearningAnAlgorithmicPerspective.jpg;type= application/octet-stream' -F 'user_data={"name":"MachineLearningAnAlgorithmicPerspective","price":"50","description":"Predictive Analytics with Microsoft Azure Machine Learning, Second Edition", "stock":"3", "category":"5"};type=application/json' -u annaheckel:mypasswor https://ec2-54-204-128-236.compute-1.amazonaws.com/addItem --cacert cert.pem -k

**Response:**

HTTP/1.0 401 UNAUTHORIZED
Content-Type: text/html; charset=utf-8
Content-Length: 19
WWW-Authenticate: Basic realm="Authentication Required"
Server: Werkzeug/1.0.1 Python/3.7.7
Date: Mon, 20 Apr 2020 19:28:04 GMT

-------------------------------------------------------------------------------------------------------

**Request:**

curl -i -X POST -H "Content-Type: multipart/form-data" -F 'image=@/home/ubuntu/MiniProject/static/images/MachineLearningAnAlgorithmicPerspective.jn/octet-stream' -F 'user_data={"name":"MachineLearningAnAlgorithmicPerspective","price":"50","description":"Predictive Analytics with Microsoft Azure Machine Learning, Second Edition", "stock":"3", "category":"5"};type=application/json' -u jamespilot:mypassword https://ec2-54-204-128-236.compute-1.amazonaws.com/addItem --cacert cert.pem -k

**Response:**

HTTP/1.0 401 UNAUTHORIZED
Content-Type: application/json
Content-Length: 52
Server: Werkzeug/1.0.1 Python/3.7.7
Date: Mon, 20 Apr 2020 19:28:32 GMT

{

"error": "only authorized user can add items"

}

-------------------------------------------------------------------------------------------------------


## **PUT:**

## **Path: /updateStockCount/<product_ID>/\<stockCount>**

**Request:**

curl -i -H "Content-Type: application/json" -X PUT -u annaheckel:mypassword https://ec2-54-204-128-236.compute-1.amazonaws.com/updateStockCount/364291/100 --cacert cert.pem -k

**Response:**

HTTP/1.0 200 OK
Content-Type: application/json
Content-Length: 47
Server: Werkzeug/1.0.1 Python/3.7.7
Date: Mon, 20 Apr 2020 19:37:43 GMT

{

"productid": "364291",

"stock": "100"

}

-------------------------------------------------------------------------------------------------------

**Request:**

curl -i -H "Content-Type: application/json" -X PUT -u annaheckel:mypassword https://ec2-54-204-128-236.compute-1.amazonaws.com/updateStockCount/364290/100 --cacert cert.pem -k

**Response:**

HTTP/1.0 404 NOT FOUND
Content-Type: application/json
Content-Length: 37
Server: Werkzeug/1.0.1 Python/3.7.7
Date: Mon, 20 Apr 2020 19:38:52 GMT

{

"error": "productId not found"

}

-------------------------------------------------------------------------------------------------------

## **DELETE:**

## **Path: /removeItem/<product_ID>**

**Request:**

curl -i -H "Content-Type:application/json" -X DELETE -u annaheckel:mypassword https://ec2-54-204-128-236.compute-1.amazonaws.com/removeItem/364291 --cacert cert.pem -k

**Response:**

HTTP/1.0 200 OK
Content-Type: application/json
Content-Length: 35
Server: Werkzeug/1.0.1 Python/3.7.7
Date: Mon, 20 Apr 2020 19:41:20 GMT

{

"success": "Product deleted"

}

**Request:**

curl -i -H "Content-Type:application/json" -X DELETE -u annaheckel:mypassword https://ec2-54-204-128-236.compute-1.amazonaws.com/removeItem/364291 --cacert cert.pem -k

**Response:**

HTTP/1.0 404 NOT FOUND
Content-Type: application/json
Content-Length: 37
Server: Werkzeug/1.0.1 Python/3.7.7
Date: Mon, 20 Apr 2020 19:43:00 GMT

{

"error": "productId not found"

}

-------------------------------------------------------------------------------------------------------
