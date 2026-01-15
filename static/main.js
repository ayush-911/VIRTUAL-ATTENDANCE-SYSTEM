let cameraStarted = false;

function toast(msg){
  const t = document.getElementById("toast");
  if(!t) return;
  t.classList.remove("hidden");
  t.textContent = msg;
  setTimeout(()=> t.classList.add("hidden"), 2500);
}

function setChip(text){
  const chip = document.getElementById("chipStatus");
  if(chip) chip.innerText = text;
}

async function startCamera(){
  const res = await fetch("/start_camera", { method:"POST" });
  const data = await res.json();

  if(data.success){
    cameraStarted = true;
    document.getElementById("videoFeed").src = "/video_feed";
    toast("✅ Camera Started");
    setChip("Live");
    startStatusLoop();
  }else{
    toast("❌ Failed to start camera");
  }
}

async function stopCamera(){
  const res = await fetch("/stop_camera", { method:"POST" });
  const data = await res.json();
  if(data.success){
    cameraStarted = false;
    document.getElementById("videoFeed").src = "";
    toast("🛑 Camera Stopped");
    setChip("Stopped");
  }
}

async function startStatusLoop(){
  while(cameraStarted){
    try{
      const res = await fetch("/status");
      const data = await res.json();

      const nameEl = document.getElementById("nameText");
      const facesEl = document.getElementById("facesText");

      if(nameEl) nameEl.innerText = data.name;
      if(facesEl) facesEl.innerText = data.faces;

      if(data.status){
        setChip(data.status);
      }
    }catch(e){}
    await new Promise(r=>setTimeout(r, 600));
  }
}

async function captureRegister(){
  const name = document.getElementById("regName").value.trim();
  if(!name){
    toast("❌ Enter name first");
    return;
  }
  const form = new FormData();
  form.append("name", name);

  const res = await fetch("/capture_register", { method:"POST", body: form });
  const data = await res.json();

  if(data.success){
    toast(data.message);
  }else{
    toast(data.message);
  }
}

async function trainModel(){
  const res = await fetch("/train", { method:"POST" });
  const data = await res.json();
  toast(data.message || "Training done");
}

async function markAttendance(){
  const res = await fetch("/mark_attendance", { method:"POST" });
  const data = await res.json();
  toast(data.message || "Done");
}

function downloadToday(){
  window.location.href = "/download_today";
}
