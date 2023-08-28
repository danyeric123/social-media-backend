# Social Media Backend

## Overview

This is the backend of a social media platform built using AWS Lambda, API Gateway, the Serverless Framework, Python, MongoDB, and Neo4j. It provides the foundation for creating, reading, updating, and deleting posts, managing user profiles, and handling relationships between users.

## Features

- **User Management**: Manage user accounts, including registration, login, and profile updates.

- **Post Management**: Create, retrieve, update, and delete posts. Posts can include text, images, and other content.

- **Follow and Unfollow**: Users can follow and unfollow other users to see their posts in their feed.

- **News Feed**: Users have a personalized news feed that shows posts from users they follow.

## Technologies Used

- **AWS Lambda**: For serverless execution of functions.

- **API Gateway**: To create HTTP endpoints.

- **Serverless Framework**: For deploying and managing serverless applications.

- **Python**: The primary programming language.

- **MongoDB**: A NoSQL database for storing user profiles and posts.

- **Neo4j**: A graph database for managing user relationships and social connections.

## Setup

1. **Install Dependencies**:
   - Install Serverless Framework: `npm install -g serverless`
   - Install Python packages: `pipenv install`

2. **Configure AWS Credentials**:
   - Configure AWS credentials with `aws configure` if not already set up.

3. **Database Configuration**:
   - Set up your MongoDB and Neo4j databases and provide connection details in the configuration files.

4. **Deploy the Backend**:
   - Run `make deploy` to deploy your Lambda functions and API Gateway.

## Endpoints

Here are some of the main endpoints provided by the API:

- `POST /register`: Register a new user.
- `POST /login`: Log in an existing user.
- `GET /users/{user_id}`: Get user profile by ID.
- `PUT /users/{user_id}`: Update user profile.
- `POST /posts`: Read news feed
- `POST /posts`: Create a new post.
- `GET /posts/{post_id}`: Get a post by ID.
- `PUT /posts/{post_id}`: Update a post.
- `DELETE /posts/{post_id}`: Delete a post.
- `POST /follow/{user_id}`: Follow a user.
- `POST /unfollow/{user_id}`: Unfollow a user.

## Testing

You can test the API using tools like `curl`, Postman, or any HTTP client. The API documentation provides detailed information about the available endpoints and their usage.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgments

- Special thanks to the Serverless Framework, MongoDB, and Neo4j communities for their fantastic tools and documentation.