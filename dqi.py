# Towards a Solution for Improving Customer Data Quality at Triodos Bank  by Lade Tawak

import streamlit as st
import re
import pandas as pd
import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException
from datetime import datetime
from rapidfuzz import process, fuzz

#dummy data
user_personal_data = {
    "first_name": "Femke",
    "last_name": "Bol",
    "email": "femke2.bol",
    "phone_number": "+32512345678",
    "street": "",
    "postcode": "3584CS",
    "city": "Utrcht",
    "account_updated_confrimed_date": "2024-01-01"
}

addresses = pd.read_csv("PC62023NL.csv") 
addresses['PC4'] = addresses['PC6'].str[:4]
pc6_set = set(addresses['PC6']) 
pc6_to_gem = {row.PC6: row.GemNaam for _, row in addresses.iterrows()} 

# Create full map and gementees list for fuzzy matching
df = addresses[['PC4', 'GemNaam']].reset_index(drop=True)
df = df.drop_duplicates(keep='first')
full_map = (df.groupby('PC4')['GemNaam'].apply(lambda s: set(s.str.lower())).to_dict())
gementees = sorted({m for munis in full_map.values() for m in munis})

#Validation and suggestion functions
email_regex = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
def is_valid_email(email):
    return bool(email_regex.match(email))

def is_valid_phone(number):
    try:
        num = phonenumbers.parse(number, "NL")
        return phonenumbers.is_valid_number(num)
    except:
        return False

def suggest_pc6(user_pc6, top_n=3, cutoff=80):
    possible_pc6 = process.extract(user_pc6.upper(), pc6_gem_set,
                           scorer=fuzz.WRatio, limit=top_n)
    return [(pc, pc6_to_gem[pc], score)
            for pc, score, _ in possible_pc6
            if score >= cutoff]

def suggest_gem(user_gem, top_n=3, cutoff=80):
    possible_gem = process.extract(user_gem.title(), gementees,
                           scorer=fuzz.token_sort_ratio, limit=top_n)
    return [(gem, score) for gem, score, _ in possible_gem if score >= cutoff]

def validate_pc6_gem(user_pc6, user_gem):
    result = {"pc6": user_pc6, "gem": user_gem}
    #check for exact pc6
    if user_pc6 in pc6_set:
        correct = pc6_to_gem[user_pc6]
        if user_gem == correct:
            result.update(status="ALL_GOOD",
                          suggestions=[])
            return result

        # if pc6 is valid but gem is wrong suggest gem typos
        g_sugg = suggest_gem(user_gem)
        result.update(status="gem_MISMATCH",
                      suggestions=[{"type":"gem","value":g} for g,_ in g_sugg])
        return result

    #if PC6 does not match any esxisting PC6, suggest PC6
    pc_sugg = suggest_pc6(user_pc6)
    if pc_sugg:
        result.update(status="PC6_SUGGEST",
                      suggestions=[{"type":"pc6","value":pc,"gem":gem,"score":scr}
                                   for pc,gem,scr in pc_sugg])
        return result
    
    #if PC6 does not match any existing PC6
    g_sugg = suggest_gem(user_gem)
    result.update(status="UNKNOWN",
                  suggestions=[{"type":"gem","value":m,"score":s} for m,s in g_sugg])
    return result


#Calculate Data Quality Score
def calculate_data_quality_score(data: dict) -> dict:
    # completeness
    fields = ['email','phone_number','street','postcode','city']
    missing = [f for f in fields if not data.get(f)]
    comp    = 1 - len(missing)/len(fields)

    # correctness
    corr_issues = []
    score_corr  = 0

    #postcode and city Validation
    pc6 = data.get('postcode')
    gem = data.get('city')

    #attempt validation if both postcode and gem are provided and are strings:
    if isinstance(pc6, str) and isinstance(gem, str) and pc6 and gem:
        validation_result = validate_pc6_gem(pc6, gem)
        status = validation_result['status']
        suggestions = validation_result.get('suggestions', [])

        if status == "ALL_GOOD":
            score_corr += 1
        else:
            # correctness issues for postcode/city based on status
            if status == "gem_MISMATCH":
                correct_gem = pc6_to_gem.get(pc6, 'N/A')
                issue_msg = f"Postcode and city do not match either because it is an incorrect city or there is a typo. Do you mean: '{correct_gem}'."
                corr_issues.append(issue_msg)


            elif status == "PC6_SUGGEST":
                issue_msg = f"Postcode '{pc6}' not found."
                corr_issues.append(issue_msg)
                if suggestions:
                     sugg = suggestions[0]
                     corr_issues.append(f"Did you mean postcode '{sugg['value']}' for '{sugg['gem']}'?")

            elif status == "UNKNOWN":
                 issue_msg = f"Postcode '{pc6}' and city '{gem}' could not be confirmed. Please check."
                 corr_issues.append(issue_msg)
                 
    else:
         if not pc6 or not isinstance(pc6, str):
             corr_issues.append("Postcode is missing.")
         if not gem or not isinstance(gem, str):
             corr_issues.append("City is missing.")
             if pc6 and isinstance(pc6, str):
                 pc4 = pc6[:4] 
                 possible_cities = full_map.get(pc4, set()) 

                 if possible_cities:
                      cities_list = sorted([city.title() for city in possible_cities]) 

                      if len(cities_list) == 1:
                           suggested_text = f"Based on postcode '{pc6}', the city is likely '{cities_list[0]}'."
                      else: 

                           suggested_text = f"Based on postcode '{pc6}', possible cities include: {', '.join(cities_list[:-1])}, or {cities_list[-1]}."

                      corr_issues.append(suggested_text)

    #Email Validation
    if is_valid_email(data.get('email', "")):
        score_corr += 1
    else:
        email_addr = data.get('email', "")
        if email_addr:
            corr_issues.append(f"Please check that your email is correct. An incorrect email address means you can't receive important updates and alerts concerning your account")
        else:
            corr_issues.append("Please enter your email address.")


    #Phone Validation
    if is_valid_phone(data.get('phone_number', "")):
        score_corr += 1
    else:
        phone_num = data.get('phone_number', "")
        if phone_num:
            corr_issues.append(f"Please check that this is your phone number, also include the country code e.g. +31")
        else:
             corr_issues.append("Phone number is missing.")


    #calculate correctness score
    correct_count = 0

    if not any("Postcode" in issue for issue in corr_issues) and not any("Municipality is missing" in issue for issue in corr_issues) and not any("Municipality is in an incorrect format" in issue for issue in corr_issues):
         correct_count += 1

    if not any("email" in issue.lower() for issue in corr_issues):
         correct_count += 1

    if not any("phone" in issue.lower() for issue in corr_issues):
         correct_count += 1

    correctness = correct_count / 3


    #Currency (linear decay over 365 days)        
    curr_issues = []
    currency = 0 # Default currency score
    checked_str = data.get('account_updated_confrimed_date')
    if checked_str:
      checked = pd.to_datetime(checked_str)
      age_days = (pd.Timestamp.now() - checked).days
      currency = max(0, 1 - age_days / 365)
      
      if age_days == 0:
        time_ago_msg = "today"
      elif age_days == 1:
        time_ago_msg = "1 day ago"
      elif age_days < 7:
        time_ago_msg = f"{age_days} days ago"
      elif age_days < 30:
        weeks = age_days // 7
        time_ago_msg = f"{weeks} weeks ago"
      elif age_days < 365:
        months = age_days // 30
        time_ago_msg = f"{months} months ago"
      else:
        time_ago_msg = f"over a year ago"
      
      curr_issues.append(f"Your personal information was last updated or confirmed {time_ago_msg}")

    #Combine Scores
    overall = 0.4*comp + 0.4*correctness + 0.2*currency

    #Issues dictionary
    issues_dict = {}
    if missing: # 
        issues_dict["completeness"] = missing
    if corr_issues: 
        issues_dict["correctness"] = corr_issues
    if curr_issues: 
        issues_dict["currency"] = curr_issues

    #No issues
    if not issues_dict:
        issues_dict["general"] = ["Your data appears up to date!"]


    return {
        "score": round(overall*100,1),
        "subscores": {
            "completeness": round(comp*100,1),
            "correctness":  round(correctness*100,1),
            "currency":     round(currency*100,1)
        },
        "issues": issues_dict 
    }


result = calculate_data_quality_score(user_personal_data)

# Streamlit App


st.title("Personal Account")


st.markdown("<h2>Your personal information quality</h2>", unsafe_allow_html=True)
st.metric(label = "Your personal information quality", value=f"{result['score']}%", delta=None)


if "general" in result['issues']:
    st.success(result['issues']['general'][0])

st.write("Your personal information is scored based on three criteria: completeness, correctness, and recency")

#expanders for issues
with st.expander("What does this mean?"):

    #missing fields
    miss = result["issues"]["completeness"]
    if miss:
        st.warning("Some information is missing: " + ", ".join(miss))
    else:
        st.success("All required fields present.")

    #correctness issues
    corr = result["issues"]["correctness"]
    if corr:
        st.error("Some fields are incorrect:")
        for note in corr:
            st.write("•", note)
    else:
        st.success("All entries look valid!")

    #recency issues
    curr = result["issues"]["currency"]
    if curr:
        st.info("Recency:")
        for note in curr:
            st.write("•", note)
    else:
        st.success("Your personal information was confirmed recently!")

    #prompt tp fix issues
    st.write("Improve your score by fixing the issues in your profile.")

#Editing information using user_personal_data
st.header("Edit Your Personal Information")

if 'user_data' not in st.session_state:
    st.session_state['user_data'] = user_personal_data 

#form for editing information
with st.form(key='personal_data_form'):
    # Create input fields pre-filled with current data 
    st.session_state['user_data']['first_name'] = st.text_input("First Name", value=st.session_state['user_data'].get('first_name', ''), key='first_name_input')
    st.session_state['user_data']['last_name'] = st.text_input("Last Name", value=st.session_state['user_data'].get('last_name', ''), key='last_name_input')
    st.session_state['user_data']['email'] = st.text_input("Email", value=st.session_state['user_data'].get('email', ''), key='email_input')
    st.session_state['user_data']['phone_number'] = st.text_input("Phone Number", value=st.session_state['user_data'].get('phone_number', ''), key='phone_number_input')
    st.session_state['user_data']['street'] = st.text_input("Street", value=st.session_state['user_data'].get('street', ''), key='street_input')
    st.session_state['user_data']['postcode'] = st.text_input("Postcode", value=st.session_state['user_data'].get('postcode', ''), key='postcode_input')
    st.session_state['user_data']['city'] = st.text_input("City", value=st.session_state['user_data'].get('city', ''), key='city_input')

    st.write(f"**Information Confirmed Date:** {st.session_state['user_data'].get('account_updated_confrimed_date', '')}")
    submitted = st.form_submit_button("Update Details")


#Calculate and display result if form has been submitted
if submitted:
    #update 'account_updated_confrimed_date' to current date
    st.session_state['user_data']['account_updated_confrimed_date'] = datetime.now().strftime('%Y-%m-%d')

    #recalculate score with updated data from session state
    result = calculate_data_quality_score(st.session_state['user_data'])
    
    #store result in session state so it persists after rerun
    st.session_state['latest_result'] = result
    
    #rerun app to display updated scores and issues
    st.rerun()

# Display most recent result. Using stored result from session state.
if 'latest_result' in st.session_state:
    st.subheader("Personal Inforamtion Quality Score After Update")

    result_to_display = st.session_state['latest_result']

    st.metric(label = "Your personal information quality",
              value = f"{result_to_display['score']}%",
              delta = None
    )
    if result_to_display['score'] == 100.0:
        st.success("Your personal information is complete, correct, and all up to date!")
        st.balloons() 
    else:
        # show suggestions 
        with st.expander("What does this mean?"):
            # Missing fields
            miss = result_to_display["issues"].get("completeness", [])
            if miss:
                st.warning("Missing fields: " + ", ".join(miss))
            else:
                st.success("All required fields present.")

            # Correctness issues
            corr = result_to_display["issues"].get("correctness", [])
            if corr:
                st.error("Correctness issues:")
                for note in corr:
                    st.write("•", note)
            else:
                st.success("All entries look accurate!")

            # recency issues
            curr = result_to_display["issues"].get("currency", [])
            if curr:
                st.info("Recency:")
                for note in curr:
                    st.write("•", note)
            else:
                st.success("Your personal information was confirmed recently!")
