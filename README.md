This is a project I worked on to improve customer data quality for Triodos bank as part of my Masters in Data Driven Design at the Hogeschool Utrecht
* dqi_phase_1.ipynb shows the first phase of explorations
* dqi_phase_2.ipynb shows the second phase of explorations
* dqi_phase_3.ipynb shows the  final solution
* dqi.py file is the streamlit file that demos the solution in streamlit

Read the [case study here](https://ladetawak.notion.site/Towards-a-Data-Quality-Indicator-DQI-to-Motivate-Triodos-Bank-Customers-to-Keep-Accurate-and-Up-to-1f84276d6db980f3a9c5f5bbf53126b5) to learn more about the project

**Problems faced by Client**

Problem given in brief
* Issues in customer addresses where postcode and city don't match although the rest of the address is real

Further research uncovered other problems and more details
* Majority of the mismatch issues occur with Dutch addresses
* customers not updating information when it changes (e.g. moving to a new house) and thus not getting the letters they request or their debit cards being delivered to old addresses
* emails sent to customers not delivering

**Impact of problems**
* Increased cost to the bank having to manually contact customers to confirm information (calls, letters etc)
* Not meeting regulatory requirements to have up to date data
* Customers don't get their documents or it gets sent to the wrong place opening them up to security risks

In this notebook, I go through the process of testing various ways of building a supervised ML model that can predict the city based on the postcode. Validate phone numbers and email address, calculate a completion score, correctness score, and currency score which will all be used to calculate the data quality score

Following the calculation, the user will be able to see this score and engage with it to improve their score

**The process looked like:**

**Phase 1**
* getting the data (first using a full address dataset from github that had over 76,000 addresses, details below)
* exploring the data
* experimenting with 3 different models (kNN, decision tree, and neural networks)

**Phase 2**
* finding another data set (from CBS, details below)
* experimenting with 5 different models and different parameters for each model (k-NN, Decision Tree, Linear Regression, Naive Bayes, and Random Forest)
* evaluating the results of each model based on accuracy etc as well as the values of the client
* using the model to assess user input and suggest corrections
* validating other data
* calculating a score
* wraping everthing in a chatbot to explain the score and suggest how they can improve their data quality

**Phase 3**
* using a postcode and municipality map from the CBS dataset to check if it's correct in the user data and using fuzzy matching for spell checks
* discarding the chatbot and replacing with updating data directly in the interface based on value sensitive design approaches
* creating a streamlit interface to show how it would work for the user

Throughout, I explain my decision making process
