// The page the router renders for any path it does not know.
import { Link } from "react-router-dom";

export const notFoundCopy = {
  documentTitle: "Off the air | Night Shift Radio",
  title: "Lost in the static",
  body: "That page went off the air. Check the schedule or head back to the live stream.",
  homeLink: "Tune back in",
  scheduleLink: "See the schedule",
} as const;

export function NotFoundPage() {
  return (
    <main className="not-found">
      <title>{notFoundCopy.documentTitle}</title>
      <h1>{notFoundCopy.title}</h1>
      <p>{notFoundCopy.body}</p>
      <nav aria-label="Ways back">
        <Link to="/" className="button button--primary">
          {notFoundCopy.homeLink}
        </Link>
        <Link to="/schedule" className="button">
          {notFoundCopy.scheduleLink}
        </Link>
      </nav>
    </main>
  );
}
