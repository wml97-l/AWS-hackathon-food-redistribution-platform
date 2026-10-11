import { Link } from 'react-router-dom';
import './Navbar.css';

function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">
          <img
            src="https://cdn.prod.website-files.com/65a64f36fd143e0af85051fb/65a64f36fd143e0af8505473_foodcloud%20on%20white.svg"
            alt="FoodCloud"
            className="navbar-logo-img"
          />
        </Link>
      </div>
    </nav>
  );
}

export default Navbar;
