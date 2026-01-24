# Bachelor's Thesis

## Introduction

The purpose of this bachelor's thesis is to develop a Telegram-based football assistant bot that provides users with football-related information using natural language interaction.  
The project focuses on integrating external data sources and AI-powered text generation to improve user experience.

The relevance of this work is explained by the increasing demand for lightweight and accessible digital solutions that do not require complex interfaces or standalone applications.

---

## Chapter 1. Analysis of the Problem Domain

### 1.1 Football Information Systems

This section describes existing football information platforms, including mobile applications, websites, and messaging-based solutions.
Football information systems are digital platforms designed to provide users with access to football-related data such as match schedules, results, league standings, and player statistics. These systems are commonly implemented as mobile applications, web platforms, or integrated services within sports media websites.

Popular football information systems focus on delivering real-time updates and comprehensive statistical data. They often integrate multiple data sources and provide advanced features such as live notifications, historical match analysis, and team performance tracking.

In recent years, the demand for instant access to sports information has increased significantly. Users expect fast, accurate, and easily accessible information across different devices and platforms. As a result, football information systems have become an essential tool for football fans worldwide.


### 1.2 Limitations of Existing Solutions

This section analyzes the disadvantages of existing football platforms, such as interface complexity, advertising overload, and limited personalization.
Despite the wide availability of football information platforms, many existing solutions have several limitations that negatively affect user experience. Mobile applications and websites often feature complex interfaces overloaded with advertisements and unnecessary functionality, which makes it difficult for users to quickly access the required information.

Another limitation of existing systems is the reliance on predefined menus and rigid interaction patterns. Users are required to navigate through multiple screens or use specific commands to retrieve information, which can be inconvenient, especially for non-technical users.

Additionally, many football information platforms lack personalization and do not adapt responses to individual user preferences. This creates a gap between the growing user demand for simple, conversational interaction and the capabilities of existing solutions.


### 1.3 Problem Statement

This section defines the main problem addressed in this project and formulates the objectives of the developed system.
The analysis of existing football information systems shows that, despite their functionality, many platforms fail to provide a simple and intuitive way for users to access football-related information. Complex interfaces, advertising overload, and rigid interaction mechanisms reduce usability and limit accessibility for a broad range of users.

There is a need for a lightweight solution that allows users to receive football information quickly without installing additional applications or navigating complex interfaces. The increasing popularity of messaging platforms creates an opportunity to deliver such functionality directly within a familiar communication environment.

The problem addressed in this project is the lack of a football information system that combines structured football data with natural language interaction in a lightweight messaging platform. To solve this problem, this project proposes the development of a Telegram-based football assistant that integrates external football data APIs and AI-powered natural language processing to provide clear and user-friendly responses.


---

## Chapter 2. System Design and Architecture

### 2.1 System Overview

This section provides a general description of the system architecture and its main components.
The developed system is a Telegram-based football assistant designed to provide users with football-related information through natural language interaction. The system follows a client-server architecture, where the Telegram messenger acts as a client interface and the backend application processes user requests and generates responses.

The core components of the system include a Telegram bot, a backend service, an external football data API, an AI language model, and a database. The Telegram bot is responsible for receiving user messages and delivering responses. The backend service processes incoming messages, determines user intent, retrieves relevant football data, and coordinates communication with external services.

Football-related data such as match schedules, results, and league standings are retrieved from an external football data API. An AI language model is used to transform structured data into human-readable responses and to support natural language interaction. User preferences and settings are stored in a database to enable personalization and notification functionality.

This modular architecture ensures scalability, maintainability, and the possibility of extending system functionality in the future.


### 2.2 Telegram Bot Architecture

The Telegram bot serves as the primary user interface of the system and is responsible for receiving user messages and delivering responses. The bot is implemented using the Telegram Bot API and operates by processing incoming updates from users.

When a user sends a message, the bot forwards the request to the backend logic for further processing. The bot does not contain complex business logic and acts as a communication layer between the user and the backend service. This separation of responsibilities improves maintainability and simplifies further development.

---

### 2.3 Integration with External APIs

Football-related information is obtained through integration with an external football data API. The API provides access to structured data such as match schedules, match results, league standings, and player statistics.

The backend service sends requests to the external API based on user queries and processes the received responses. Error handling mechanisms are implemented to manage cases where the external API is unavailable or returns incomplete data.

---

### 2.4 AI-powered Natural Language Processing

AI-powered natural language processing is used to improve user interaction with the system. The AI component processes user queries written in natural language and helps determine the intent of the request.

Additionally, the AI language model is used to generate human-readable responses based on structured football data. This approach allows the system to present information in a conversational and user-friendly manner without requiring users to use predefined commands.

---

### 2.5 Database Design

The system uses a relational database to store user-related data and preferences. The database includes information about users, selected favorite teams, and notification settings.

Storing user data enables personalization features and allows the system to provide relevant notifications. The database structure is designed to be simple and efficient, ensuring fast data access and scalability.

---

## Chapter 3. System Implementation

### 3.1 Development Environment

The system is developed using the Python programming language. Development tools include an integrated development environment, version control system, and external libraries required for bot development and API integration.

Git and GitHub are used for version control, enabling safe code management and collaboration. The development environment supports modular design and incremental implementation.

---

### 3.2 Bot Functionality Implementation

The core functionality of the Telegram bot includes processing user messages, retrieving football data, and sending responses. User requests are analyzed to determine the type of information required, after which relevant data is retrieved from external services.

The bot supports multiple functional scenarios, including retrieving match schedules, match results, league standings, and player statistics. User preferences are applied during response generation to provide personalized information.

---

### 3.3 AI Integration Implementation

The AI integration is implemented by connecting the backend service to an AI language model through an API. The AI component processes structured football data and generates natural language responses.

This approach allows the system to separate data retrieval from response generation, improving flexibility and simplifying future enhancements. AI integration enhances usability while maintaining system reliability.

---

## Chapter 4. Testing and Evaluation

### 4.1 Functional Testing

Functional testing is conducted to verify that all system features operate as expected. Test cases include checking message processing, data retrieval from external APIs, AI response generation, and notification delivery.

Testing ensures that the system responds correctly to valid user requests and handles incorrect or incomplete inputs gracefully.

---

### 4.2 System Evaluation

The system is evaluated based on usability, response time, and reliability. The use of a messaging platform ensures accessibility, while AI-powered responses improve user experience.

Evaluation results demonstrate that the developed system meets the defined project goals and provides a convenient solution for accessing football-related information.

---

## Conclusion

This bachelor's thesis presented the development of a Telegram-based football assistant that provides football-related information using natural language interaction. The system integrates external football data APIs and AI-powered text generation to improve accessibility and usability.

The developed solution demonstrates the feasibility of combining messaging platforms with AI technologies to create lightweight and user-friendly information systems. Future improvements may include expanding league coverage, enhancing personalization, and adding advanced notification features.

---

## References

1. Telegram Bot API Documentation  
2. Python Programming Language Documentation  
3. Football Data API Documentation  
4. AI Language Model API Documentation
