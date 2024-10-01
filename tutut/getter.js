const redis = require('redis');

// Define Redis connection details
const redisUrl = 'redis://103.59.95.141:6379';

// Create a Redis client using the URL
const client = redis.createClient({
  url: redisUrl
});

client.on('error', (err) => console.log('Redis Client Error', err));

// Async function to connect and get data using a dynamic key
async function getDataFromRedis() {
  await client.connect();
  console.log('Connected to Redis');

  // Define the key to retrieve data dynamically
  const key = 'username'; // Change this key as needed

  try {
    // Get the value from Redis using the dynamic key
    const value = await client.get(key);
    if (value) {
      console.log(`Value for key "${key}":`, JSON.parse(value));
    } else {
      console.log(`No value found for key "${key}".`);
    }
  } catch (error) {
    console.error(`Error getting value for key "${key}":`, error);
  } finally {
    // Close the client connection
    await client.quit();
  }
}

// Call the function to get data from Redis
getDataFromRedis();
