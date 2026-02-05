import RequestBuilder from "../components/playground/RequestBuilder";

export default function PlaygroundPage() {
  return (
    <div>
      <h1>API Playground</h1>
      <p>Build and send requests against the simulation APIs.</p>
      <RequestBuilder />
    </div>
  );
}
