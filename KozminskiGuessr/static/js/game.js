let photos = [];
let currentRound = 0;
let scores = [];
let totalScore = 0;

async function startGame() {
    const response = await fetch('/api/get_photos');
    photos = await response.json();
    currentRound = 0;
    scores = [];
    totalScore = 0;
    document.getElementById('score-ticker').textContent = `Score: ${totalScore}`;
    document.getElementById('summary').style.display = 'none';
    showRound();
}

function showRound() {
    if (currentRound < 5) {
        const img = document.getElementById('classroom-image');
        img.src = photos[currentRound].image_url;
        resetInputs();
        const btn = document.getElementById('guess-btn');
        btn.style.backgroundImage = "url('/static/images/button_guess.png')";
        btn.onclick = makeGuess;
        document.getElementById('feedback').innerHTML = '';
        document.getElementById('round-counter').textContent = `Round: ${currentRound + 1}/5`;
    } else {
        showSummary();
    }
}

function resetInputs() {
    const building = document.getElementById('building');
    const floor = document.getElementById('floor');
    const classroom = document.getElementById('classroom');
    building.value = '';
    floor.value = '';
    classroom.value = '';
    building.classList.remove('correct', 'incorrect');
    floor.classList.remove('correct', 'incorrect');
    classroom.classList.remove('correct', 'incorrect');
}

async function makeGuess() {
    const building = document.getElementById('building').value;
    const floor = document.getElementById('floor').value;
    const classroom = document.getElementById('classroom').value;

    if (!building && !floor && !classroom) {
        if (!confirm('No guesses made. Proceed with 0 points?')) return;
    }

    const response = await fetch('/api/guess', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ photo_id: photos[currentRound].id, building, floor, classroom })
    });
    const result = await response.json();

    scores.push(result.score);
    totalScore += result.score;
    document.getElementById('score-ticker').textContent = `Score: ${totalScore}`;

    displayFeedback(result);
    if (currentRound === 4) {
        // Show the "Play Again" button directly after the last guess
        const btn = document.getElementById('guess-btn');
        btn.style.backgroundImage = "url('/static/images/play_again_button.png')";
        btn.onclick = startGame;
    } else {
        // Otherwise, show the "Next Round" button
        const btn = document.getElementById('guess-btn');
        btn.style.backgroundImage = "url('/static/images/next_round_button.png')";
        btn.onclick = nextRound;
    }
}

function nextRound() {
    currentRound++;
    if (currentRound < 5) {
        showRound();
        const btn = document.getElementById('guess-btn');
        btn.style.backgroundImage = "url('/static/images/button_guess.png')"; // switch back to GUESS button image
        btn.onclick = makeGuess; // set the click back to guessing
    } else {
        showSummary();
    }
}

function displayFeedback(result) {
    const building = document.getElementById('building');
    const floor = document.getElementById('floor');
    const classroom = document.getElementById('classroom');
    
    // Remove previous feedback classes
    building.classList.remove('correct', 'incorrect');
    floor.classList.remove('correct', 'incorrect');
    classroom.classList.remove('correct', 'incorrect');
    
    // Apply new feedback classes
    if (result.correct || result.correct_building === building.value) {
        building.classList.add('correct');
    } else {
        building.classList.add('incorrect');
    }
    if (result.correct || result.correct_floor === parseInt(floor.value)) {
        floor.classList.add('correct');
    } else {
        floor.classList.add('incorrect');
    }
    if (result.correct || result.correct_classroom === classroom.value) {
        classroom.classList.add('correct');
    } else {
        classroom.classList.add('incorrect');
    }

    let feedback = `<p>Score: ${result.score}</p>`;
    if (!result.correct) {
        feedback += `<p>Correct: ${result.correct_classroom} (Building ${result.correct_building}, Floor ${result.correct_floor})</p>`;
    }
    document.getElementById('feedback').innerHTML = feedback;
}

async function showSummary() {
    await fetch('/api/save_score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ score: totalScore })
    }).then(res => res.json()).then(data => {
        const summary = document.getElementById('summary');
        summary.style.display = 'block';
        summary.innerHTML = 
            `<h2>Game Summary</h2>
            ${scores.map((s, i) => `<p>Round ${i + 1}: ${s} points</p>`).join('')}
            <p>Total Score: ${totalScore}</p>
            <p>Your High Score: ${data.high_score}</p>`;

        const btn = document.getElementById('guess-btn');
        btn.style.backgroundImage = "url('/static/images/play_again_button.png')"; // Set the Play Again button image
        btn.onclick = startGame; // Call startGame when clicked
      
    });
}

async function updateClassroomList() {
    const building = document.getElementById('building').value;
    const floor = document.getElementById('floor').value;
    const classroom = document.getElementById('classroom').value;
    const response = await fetch(`/api/classrooms?building=${building}&floor=${floor}&filter=${classroom}`);
    const classrooms = await response.json();
    const datalist = document.getElementById('classroom-list');
    datalist.innerHTML = classrooms.map(c => `<option value="${c.classroom_number}">`).join('');
}

document.addEventListener('DOMContentLoaded', () => {
    startGame();
    document.getElementById('building').addEventListener('change', updateClassroomList);
    document.getElementById('floor').addEventListener('change', updateClassroomList);
    document.getElementById('classroom').addEventListener('input', updateClassroomList);
});

async function startGame() {
    const response = await fetch('/api/get_photos');
    photos = await response.json();
    currentRound = 0;
    scores = [];
    totalScore = 0;
    document.getElementById('score-ticker').textContent = `Score: ${totalScore}`;
    document.getElementById('summary').style.display = 'none';
    showRound(); // Reset the round flow
}