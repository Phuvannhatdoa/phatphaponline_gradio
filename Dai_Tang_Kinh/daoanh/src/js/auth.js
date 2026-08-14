// Authentication handler - Basic Auth with GraphDB
const Auth = {
    /**
     * Login with Basic Auth credentials
     */
    login: function(username, password) {
        // Store credentials (Base64 encoded for Basic Auth)
        const credentials = btoa(`${username}:${password}`);
        
        // Test authentication by querying GraphDB
        return fetch(CONFIG.GRAPHDB.sparqlUrl + "?query=SELECT%20%3Fs%20WHERE%20%7B%3Fs%20a%20%3Ftype%7D%20LIMIT%201", {
            method: "GET",
            headers: {
                "Authorization": `Basic ${credentials}`,
                "Accept": "application/sparql-results+json"
            }
        })
        .then(response => {
            if (response.ok) {
                // Save auth to localStorage
                localStorage.setItem(CONFIG.AUTH_KEY, JSON.stringify({
                    username: username,
                    credentials: credentials,
                    timestamp: Date.now()
                }));
                return { success: true, username: username };
            } else {
                throw new Error("Authentication failed");
            }
        })
        .catch(error => {
            console.error("Login error:", error);
            throw error;
        });
    },
    
    /**
     * Check if user is logged in
     */
    isLoggedIn: function() {
        const auth = localStorage.getItem(CONFIG.AUTH_KEY);
        if (!auth) return false;
        
        const authData = JSON.parse(auth);
        
        // Check if session is recent (24 hours)
        const dayInMs = 24 * 60 * 60 * 1000;
        if (Date.now() - authData.timestamp > dayInMs) {
            this.logout();
            return false;
        }
        
        return authData;
    },
    
    /**
     * Get stored credentials
     */
    getCredentials: function() {
        const auth = localStorage.getItem(CONFIG.AUTH_KEY);
        if (!auth) return null;
        return JSON.parse(auth).credentials;
    },
    
    /**
     * Get username
     */
    getUsername: function() {
        const auth = localStorage.getItem(CONFIG.AUTH_KEY);
        if (!auth) return null;
        return JSON.parse(auth).username;
    },
    
    /**
     * Logout
     */
    logout: function() {
        localStorage.removeItem(CONFIG.AUTH_KEY);
        window.location.href = "index.html";
    }
};