class SessionStore:
    def __init__(self):
        self._sessions = {}

    def ensure(self, user_id: int):
        session = self._sessions.setdefault(
            user_id,
            {
                "screen": "main",
                "payload": {},
                "history": [],
                "anchor_message_id": None,
            },
        )
        return session

    def set_anchor(self, user_id: int, message_id: int):
        self.ensure(user_id)["anchor_message_id"] = message_id

    def get_anchor(self, user_id: int):
        return self.ensure(user_id)["anchor_message_id"]

    def set_screen(self, user_id: int, screen: str, payload: dict | None = None, reset: bool = False):
        session = self.ensure(user_id)
        if reset:
            session["history"] = []
        else:
            session["history"].append(
                {
                    "screen": session["screen"],
                    "payload": session["payload"],
                }
            )

        session["screen"] = screen
        session["payload"] = payload or {}
        return session

    def replace_screen(self, user_id: int, screen: str, payload: dict | None = None):
        session = self.ensure(user_id)
        session["screen"] = screen
        session["payload"] = payload or {}
        return session

    def back(self, user_id: int):
        session = self.ensure(user_id)
        if session["history"]:
            previous = session["history"].pop()
            session["screen"] = previous["screen"]
            session["payload"] = previous["payload"]
        else:
            session["screen"] = "main"
            session["payload"] = {}
        return session

    def current_screen(self, user_id: int):
        return self.ensure(user_id)["screen"]

    def current_payload(self, user_id: int):
        return self.ensure(user_id)["payload"]
