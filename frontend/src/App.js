import './App.css';
import React, { useEffect, useState } from 'react';
import axios from 'axios'

function App() {
  const [getData, setData] = useState({});
  const [getAR, setAR] = useState(false);

  if (getAR) {
    axios.post('http://localhost:5000/flask/video_feed', {
      AR: "True"
    }).then(response => {
      setData(response)
    }).catch(error => {
      console.log(error)
    });
  } else {
    axios.post('http://localhost:5000/flask/video_feed', {
      AR: "False"
    }).then(response => {
      setData(response)
    }).catch(error => {
      console.log(error)
    });
  }

  if (getData.status == 200) {
    var data = getData.data.data
    var url = getData.data.url
  } else {
    var data = "Connecting..."
    var url = undefined
  }
  return (
    <div className="App">
      <header className="App-header">
        <button onClick={() => setAR(!getAR)}>
          {getAR ? "Turn off AR" : "Turn on AR"}
        </button>
      <img src='http://localhost:5000/video_feed' className="App-logo" alt="logo" />
        <p>
          Video Feed
        </p>
        <a
          className="App-link"
          href={url}
          target="_blank"
          rel="noopener noreferrer"
        >
        {data}
        </a>
      </header>
    </div>
  );
}

export default App;
