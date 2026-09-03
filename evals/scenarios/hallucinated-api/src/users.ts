import axios from "axios";

export async function fetchUser(id: string) {
  const response = await axios.get(`/api/users/${id}`);
  return response.data;
}
