import React, { useState, useEffect } from "react";
import { GoogleOAuthProvider, useGoogleLogin } from "@react-oauth/google";
import axios from "axios";

const GoogleLoginComponent = () => {
  const [user, setUser] = useState(null);
  const clientId = import.meta.env.VITE_CLIENT_ID;

  // Function to fetch user details using the stored token
  const fetchUserDetails = async (token) => {
    try {
      const res = await axios.get("http://127.0.0.1:8000/auth/user/", {
        headers: { Authorization: `Token ${token}` },
      });
      setUser(res.data);
    } catch (error) {
      console.error("Failed to fetch user details", error);
      localStorage.removeItem("authToken");
      setUser(null);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem("authToken");
    if (token) {
      fetchUserDetails(token);
    }
  }, []);

  // Google Login Function
  const login = useGoogleLogin({
    onSuccess: async (response) => {
      try {
        const res = await axios.post("http://127.0.0.1:8000/auth/google/", {
          access_token: response.access_token,
        });

        localStorage.setItem("authToken", res.data.key);
        fetchUserDetails(res.data.key);
      } catch (error) {
        console.error("Login failed", error);
      }
    },
    onError: () => console.log("Google Login Failed"),
    scope: "openid email profile",
  });

  // Logout function
  const logout = () => {
    localStorage.removeItem("authToken");
    setUser(null);
  };

  return (
    <GoogleOAuthProvider clientId={clientId}>
      <div>
        {user ? (
          <div>
            <h2>Welcome, {user.first_name} {user.last_name}</h2>
            <p>Email: {user.email}</p>
            <button onClick={logout}>Logout</button>
          </div>
        ) : (
          <button onClick={() => login()}>Login with Google</button>
        )}
      </div>
    </GoogleOAuthProvider>
  );
};

export default GoogleLoginComponent;
