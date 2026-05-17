from datetime import datetime
from typing import List
import os
import requests
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException,status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine,Column,Integer,String,DateTime,Float
from sqlalchemy.orm import sessionmaker, declarative_base, Session

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

if not OPENWEATHER_API_KEY:
      print("warning")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = "sqlite:///./weather.db"
engine =create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread":False},
)

SessionLocal =sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base=declarative_base()

#db model
class WeatherSearch(Base):
    __tablename__="weather_searches"

    id= Column(Integer, primary_key=True, index=True)
    city_name= Column(String,nullable=False)
    latitude=Column(Float,nullable=False)
    longitude=Column(Float,nullable=False)
    temperature=Column(Float,nullable=False)
    feels_like=Column(Float,nullable=False)
    humidity=Column(Integer,nullable=False)
    weather_main=Column(String,nullable=False)
    weather_description=Column(String,nullable=False)
    wind_speed=Column(Float,nullable=False)
    searched_at=Column(DateTime,default=datetime.utcnow)

Base.metadata.create_all(bind=engine)


def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

class WeatherSearchRequest(BaseModel):
        city:str           

class WeatherResponse(BaseModel):
      id:int
      city_name:str
      latitude:float
      longitude:float
      temperature:float
      feels_like:float
      humidity:int
      weather_main:str
      weather_description:str
      wind_speed:float
      searched_at:datetime

      class Config:
            from_attributes=True

class DeleteResponse(BaseModel):
      message:str


def fetch_weather_from_openweather(city:str):
      
      if not OPENWEATHER_API_KEY:
            raise HTTPException(
                  status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                  detail="OpenWeather API key is not configured",
            )
      
      url = "https://api.openweathermap.org/data/2.5/weather"
      params = {
            "q":city,
            "appid":OPENWEATHER_API_KEY,
            "units":"metric",
      }
      
      try:
            response = requests.get(url,params=params,timeout=10)
      except requests.RequestException:
            raise HTTPException(
                  status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                  detail="unable to connect"
            )
      
      if response.status_code==404:
            raise HTTPException(
                  status_code=status.HTTP_404_NOT_FOUND,
                  detail="city not found"
            )
      if response.status_code!=200:
            raise HTTPException(
                  status_code=status.HTTP_502_BAD_GATEWAY,
                  detail=f"failed to fetch weather data from OpenWeather: {response.status_code}"
            )
      return response.json()


@app.get("/")
def root():
      return{
            "message":"Weather Explorer API is running"
      }

@app.post(
      "/weather/search",
      response_model=WeatherResponse,
      status_code=status.HTTP_201_CREATED,
)
def search_weather_and_save(
      request:WeatherSearchRequest,
      db: Session =Depends(get_db),
):
      city=request.city.strip()

      if not city:
            raise HTTPException(
                  status_code=status.HTTP_400_BAD_REQUEST,
                  detail="city name cannot be empty"
            )
      weather_data=fetch_weather_from_openweather(city)
      weather = weather_data["weather"][0]

      new_weather_search = WeatherSearch(
            city_name=weather_data["name"],
            latitude=weather_data["coord"]["lat"],
            longitude=weather_data["coord"]["lon"],
            temperature=weather_data["main"]["temp"],
            feels_like=weather_data["main"]["feels_like"],
            humidity=weather_data["main"]["humidity"],
            weather_main=weather["main"],
            weather_description=weather["description"],
            wind_speed=weather_data["wind"]["speed"],
      )
      db.add(new_weather_search)
      db.commit()
      db.refresh(new_weather_search)

      return new_weather_search

@app.get(
      "/weather",
      response_model=List[WeatherResponse],
)
def get_all_saved_weather(
    db:Session = Depends(get_db),
):
      saved_weather =(
            db.query(WeatherSearch)
            .order_by(WeatherSearch.searched_at.desc())
            .all()
      )
      return saved_weather

@app.get(
      "/weather/{weather_id}",
      response_model=WeatherResponse,
)
def get_saved_weather_by_id(
      weather_id:int,
      db:Session=Depends(get_db),

):
      weather_record=(
            db.query(WeatherSearch)
            .filter(WeatherSearch.id ==weather_id)
            .first()
      )
      return weather_record
