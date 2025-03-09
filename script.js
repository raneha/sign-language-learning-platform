const urlParams = new URLSearchParams(window.location.search);
const level = urlParams.get("level") || 1;

const levelLetters = {
    1: ["A", "B", "C", "E", "L", "O", "V", "W", "U", "Y"],
    2: ["D", "F", "K", "R", "S", "I", "T"],
    3: ["G", "H", "M", "N", "X"],
    4: ["P", "Q", "Z", "J"]
};

document.getElementById("letterList").innerText = levelLetters[level].join(", ");

let score = 0;
let highScore = localStorage.getItem("highScore") || 0;
let currentIndex = 0;  

document.getElementById("highScore").innerText = highScore;

function startCamera() {
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => { document.getElementById("video").srcObject = stream; })
        .catch(err => console.error("Camera access denied:", err));
}

function startGame() {
    document.querySelector(".overlay").style.display = "none";  
    document.querySelector(".game-container").style.display = "flex";  

    currentIndex = 0; 
    document.getElementById("gameLetter").innerText = levelLetters[level][currentIndex]; 
    currentIndex++; 
    startCamera();
}

function nextLetter() {
    if (currentIndex < levelLetters[level].length) {
        document.getElementById("gameLetter").innerText = levelLetters[level][currentIndex]; 
        score++;  
        document.getElementById("score").innerText = score;  
        currentIndex++;  
    } else {
        alert(`Level ${level} Complete!`);  
        currentIndex = 0;  
    }
}

function skipLetter() {
    if (currentIndex < levelLetters[level].length) {
        document.getElementById("gameLetter").innerText = levelLetters[level][currentIndex]; 
        currentIndex++;  
    } else {
        alert(`Level ${level} Complete!`);  
        currentIndex = 0;  
    }
}

function finishGame() {
    if (score > highScore) {
        highScore = score;
        localStorage.setItem("highScore", highScore);
    }
    alert(`Game Over! Your Score: ${score}\nHighest Score: ${highScore}`);
    score = 0;
    document.getElementById("score").innerText = score;
}
