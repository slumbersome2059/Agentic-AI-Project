import { GoogleGenAI } from "@google/genai";
console.log("hello")
const ai = new GoogleGenAI({});
async function main() {
  const response = await ai.models.generateContent({
    model: "gemini-2.5-flash",
    contents: "Give me a route from CB2 1DQ",
  });
  console.log(response.text);
}
