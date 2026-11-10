const form = document.getElementById("chatForm");
const input = document.getElementById("messageInput");
const imageInput = document.getElementById("imageInput");
const attachButton = document.getElementById("attachButton");
const sendButton = document.getElementById("sendButton");
const messages = document.getElementById("messages");
const welcome = document.getElementById("welcome");
const preview = document.getElementById("attachmentPreview");
const newChatButton = document.getElementById("newChatButton");
const menuButton = document.getElementById("menuButton");
const sidebar = document.querySelector(".sidebar");

let selectedImage = null;
let selectedImageUrl = null;
let busy = false;
let conversation = [];

function addMessage(text, imageUrl, author) {
  const row = document.createElement("div");
  row.className = "message " + author;
  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = author === "user" ? "V" : "D";
  const content = document.createElement("div");
  content.className = "message-content";
  if (text) content.textContent = text;
  if (imageUrl) {
    const image = document.createElement("img");
    image.src = imageUrl;
    image.alt = "Imagem enviada";
    content.appendChild(image);
  }
  if (author === "user") row.append(content, avatar);
  else row.append(avatar, content);
  messages.appendChild(row);
  row.scrollIntoView({ behavior: "smooth", block: "end" });
  return row;
}

function clearAttachment() {
  selectedImage = null;
  if (selectedImageUrl) URL.revokeObjectURL(selectedImageUrl);
  selectedImageUrl = null;
  imageInput.value = "";
  preview.hidden = true;
  preview.replaceChildren();
}

function setBusy(value) {
  busy = value;
  sendButton.disabled = value;
  input.disabled = value;
  sendButton.textContent = value ? "…" : "↑";
}

attachButton.addEventListener("click", () => imageInput.click());

imageInput.addEventListener("change", () => {
  const file = imageInput.files && imageInput.files[0];
  if (!file || !file.type.startsWith("image/")) return;
  selectedImage = file;
  if (selectedImageUrl) URL.revokeObjectURL(selectedImageUrl);
  selectedImageUrl = URL.createObjectURL(file);
  preview.hidden = false;
  preview.replaceChildren();
  const image = document.createElement("img");
  image.src = selectedImageUrl;
  image.alt = "Prévia da imagem";
  const name = document.createElement("span");
  name.textContent = file.name;
  const remove = document.createElement("button");
  remove.type = "button";
  remove.textContent = "Remover";
  remove.addEventListener("click", clearAttachment);
  preview.append(image, name, remove);
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy) return;
  const text = input.value.trim();
  if (!text && !selectedImage) return;

  welcome.hidden = true;
  const imageUrl = selectedImageUrl;
  addMessage(text || "Imagem enviada.", imageUrl, "user");
  input.value = "";
  input.style.height = "auto";
  clearAttachment();

  if (!text) {
    addMessage("No momento, o Dexbot recebe texto. O envio de imagens ainda não está ligado ao modelo.", null, "assistant");
    return;
  }

  conversation.push({ role: "user", content: text });
  const typing = addMessage("Pensando…", null, "assistant");
  setBusy(true);

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: conversation.slice(-30) })
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || "Falha ao conversar com o servidor.");
    if (!data.response) throw new Error("O servidor respondeu sem texto.");
    typing.querySelector(".message-content").textContent = data.response;
    conversation.push({ role: "assistant", content: data.response });
  } catch (error) {
    typing.querySelector(".message-content").textContent =
      "Não consegui alcançar o Dexbot no PC. " + (error.message || "Verifique se o servidor e o túnel estão ligados.");
    conversation.pop();
  } finally {
    setBusy(false);
    input.focus();
  }
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 150) + "px";
});

document.querySelectorAll(".suggestion").forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.dataset.prompt || "";
    input.focus();
  });
});

newChatButton.addEventListener("click", () => {
  messages.replaceChildren();
  welcome.hidden = false;
  clearAttachment();
  input.value = "";
  conversation = [];
  sidebar.classList.remove("open");
});

menuButton.addEventListener("click", () => sidebar.classList.toggle("open"));
