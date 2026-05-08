export const removeChatSession = () => {
  sessionStorage.removeItem("chat_messages");
  const url = new URL(window.location.href);

  if (url.searchParams.has("thread_id")) {
    url.searchParams.delete("thread_id");

    window.history.replaceState({}, "", url.toString());
  }
};
