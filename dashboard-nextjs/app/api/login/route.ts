// pages/api/login.js
import axios from 'axios';
import { NextResponse } from 'next/server';
import { serialize } from 'cookie';

const loginEndpoint = 'http://localhost:5003/login'; // Replace with your actual backend URL

export async function POST(request : any) {
  try {
    const { username, password } = await request.json();

    // Send login request to the backend server
    const response = await axios.post(loginEndpoint, { username, password });
    const { token } = response.data;

    // Set token in cookies (valid for 2 hours)
    const cookie = serialize('access-token', token, {
      httpOnly: true,
      maxAge: 2 * 60 * 60, // 2 hours in seconds
      path: '/',
    });

    // Return response with the token cookie
    return new NextResponse(JSON.stringify({ success: true }), {
      status: 200,
      headers: { 'Set-Cookie': cookie },
    });
  } catch (error) {
    return new NextResponse(JSON.stringify({ success: false, message: 'Login failed' }), {
      status: 401,
    });
  }
}
