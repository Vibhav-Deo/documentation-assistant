class SimpleConversation:
    def __init__(self):
        self.sessions = {}
    
    def create_session(self): 
        session_id = f"session_{len(self.sessions)}"
        self.sessions[session_id] = []
        return session_id
    
    def add_message(self, session_id, question, answer, sources): 
        if session_id not in self.sessions:
            session_id = self.create_session()
        self.sessions[session_id].append({"q": question, "a": answer})
        return session_id
    
    def get_context(self, session_id): 
        if session_id in self.sessions:
            return "\n".join([f"Q: {m['q']}\nA: {m['a']}" for m in self.sessions[session_id][-2:]])
        return ""