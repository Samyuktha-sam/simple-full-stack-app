import { useState } from "react";

function App() {
  const [city, setCity] = useState("");
  const [weather, setWeather] = useState(null);
  const [error, setError] = useState("");

  const handleSearch = async () => {
    try {
      setError("");
      setWeather(null);

      const response = await fetch("http://127.0.0.1:8000/weather/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ city }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to fetch weather data");
      }

      setWeather(data);
    } catch (err) {
      console.log(err);
      setError(err.message || "Failed to fetch weather data");
    }
  };

  return (
    <div style={{ padding: "40px", fontFamily: "Arial" }}>
      <h1>Weather App</h1>

      <input
        type="text"
        placeholder="Enter city name"
        value={city}
        onChange={(e) => setCity(e.target.value)}
        style={{ padding: "10px", marginRight: "10px" }}
      />

      <button onClick={handleSearch} style={{ padding: "10px 18px" }}>
        Search
      </button>

      {error && <p style={{ color: "red" }}>{error}</p>}

      {weather && (
        <div style={{ marginTop: "30px" }}>
          <h2>{weather.city_name}</h2>
          <p>Temperature: {weather.temperature} °C</p>
          <p>Feels Like: {weather.feels_like} °C</p>
          <p>Humidity: {weather.humidity}%</p>
          <p>Weather: {weather.weather_description}</p>
          <p>Wind Speed: {weather.wind_speed} m/s</p>
          <p>Latitude: {weather.latitude}</p>
          <p>Longitude: {weather.longitude}</p>
        </div>
      )}
    </div>
  );
}

export default App;
