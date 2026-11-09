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
  if (author === "user") {
    row.append(content, avatar);
  } else {
    row.append(avatar, content);
  }
  messages.appendChild(row);
  row.scrollIntoView({ behavior: "smooth", block: "end" });
}

function clearAttachment() {
  selectedImage = null;
  if (selectedImageUrl) URL.revokeObjectURL(selectedImageUrl);
  selectedImageUrl = null;
  imageInput.value = "";
  preview.hidden = true;
  preview.replaceChildren();
}

attachButton.addEventListener("click", () => imageInput.click());

imageInput.addEventListener("change", () => {
  const file = imageInput.files && imageInput.files[0];
  if (!file) return;
  if (!file.type.startsWith("image/")) return;
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

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text && !selectedImage) return;
  welcome.hidden = true;
  const imageUrl = selectedImageUrl;
  addMessage(text, imageUrl, "user");
  input.value = "";
  input.style.height = "auto";
  clearAttachment();
  addMessage("Recebi sua mensagem! A interface já está pronta para receber a conexão com o mecanismo de IA. Essa conexão será adicionada na próxima etapa.", null, "assistant");
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
  sidebar.classList.remove("open");
});

menuButton.addEventListener("click", () => sidebar.classList.toggle("open"));
