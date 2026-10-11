import StockAlerts from '../components/StockAlerts';
import GapAnalysis from '../components/GapAnalysis';
import DistributionAnalytics from '../components/DistributionAnalytics';
import './Dashboard.css';

function Dashboard() {
  return (
    <div className="dashboard">
      <header className="page-header">
        <h1>MealMap</h1>
        <p>Overview of food donations and member distribution requests</p>
      </header>

      <StockAlerts />
      <GapAnalysis />
      <DistributionAnalytics />
    </div>
  );
}

export default Dashboard;
