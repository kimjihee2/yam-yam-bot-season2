import streamlit as st
from openai import OpenAI 
import requests
from geopy.geocoders import Nominatim

# Streamlit 앱 초기 설정
st.markdown("<h1 style='text-align: center;'>What is your tasty?</h1>", unsafe_allow_html=True)
st.write(
    "This is a simple chatbot that uses OpenAI's GPT-3.5 model to generate restaurant suggestions. "
    "To use this app, you need to provide API keys for both OpenAI and Google Maps."
)

# API 키 입력받기
openai_api_key = st.text_input("OpenAI API Key", type="password")
google_maps_api_key = st.text_input("Google Maps API Key", type="password")

def find_restaurants(location, google_maps_api_key, keyword, radius=1500, type='restaurant'):
    # Google Maps API를 사용하여 맛집 찾기
    google_maps_url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
    params = {
        'key': google_maps_api_key,
        'location': location,
        'radius': radius,
        'type': type,
        'keyword':keyword
    }

    response = requests.get(google_maps_url, params=params)
    results = response.json().get('results', [])

    restaurants = []
    for result in results[:3]:
        restaurants.append(f"{result['name']} - {result['vicinity']}")

    return restaurants

def get_lat_lon(city_name):
    geolocator = Nominatim(user_agent="dishfinder")
    location = geolocator.geocode(city_name)
    if location is not None:
        return location.latitude, location.longitude
    else:
        raise ValueError("해당 위치를 찾을 수 없습니다.")

if not openai_api_key or not google_maps_api_key:
    st.info("Please add your OpenAI and Google Maps API keys to continue.", icon="🗝️")
else:
    client = OpenAI(api_key=openai_api_key)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):


            st.markdown(message["content"])

    city_name = st.text_input("도시 이름을 입력해주세요 (예: Seoul, San Francisco):")
    user_input = st.chat_input("What type of restaurant are you looking for?")
    
    if city_name and user_input:
        # 사용자 입력 저장
        st.session_state.messages.append({"role": "user", "content": f"City: {city_name}, Type: {user_input}"})
        with st.chat_message("user"):
            st.markdown(f"City: {city_name}, Type: {user_input}")

        try:
            lat, lon = get_lat_lon(city_name)
            location = f"{lat},{lon}"
            with st.spinner('추천 맛집 찾는 중...'):
                restaurants = find_restaurants(location, google_maps_api_key,keyword=user_input)
            
            # 맛집 검색 결과 출력
            st.write("### 주변의 추천 맛집:")
            for restaurant in restaurants:
                st.write(restaurant)

            # OpenAI API를 통해 추가 추천
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You're a helpful assistant that enhances restaurant suggestions."},
                    {"role": "user", "content": f"Suggest more about {user_input} restaurants in {city_name}. Here are some nearby options: {', '.join(restaurants)}"}
                ],
                max_tokens=150
            )

            gpt_response = response.choices[0].message.content
            
            with st.chat_message("assistant"):
                st.markdown(gpt_response)

            st.session_state.messages.append({"role": "assistant", "content": gpt_response})

        except Exception as e:
            st.error(f"문제가 발생했습니다: {e}")
