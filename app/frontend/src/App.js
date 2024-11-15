import React, { useState } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Box, AppBar, Toolbar, IconButton, Typography, Drawer, List, ListItem, ListItemIcon, ListItemText } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import LeaderboardIcon from '@mui/icons-material/Leaderboard';
import SportsFootballIcon from '@mui/icons-material/SportsFootball';
import BarChartIcon from '@mui/icons-material/BarChart';
import SettingsIcon from '@mui/icons-material/Settings';

// Import components
import Login from './components/Login';
import Leaderboard from './components/Leaderboard';
import WeeklyPicks from './components/WeeklyPicks';
import Statistics from './components/Statistics';
import Settings from './components/Settings';
import { AuthProvider, useAuth } from './contexts/AuthContext';

const menuItems = [
  { text: 'Leaderboard', icon: <LeaderboardIcon />, path: '/' },
  { text: 'Weekly Picks', icon: <SportsFootballIcon />, path: '/picks' },
  { text: 'Statistics', icon: <BarChartIcon />, path: '/stats' },
  { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
];

function PrivateRoute({ children }) {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  return isAuthenticated ? (
    children
  ) : (
    <Navigate to="/login" state={{ from: location }} replace />
  );
}

function App() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { isAuthenticated, user } = useAuth();

  const toggleDrawer = () => {
    setDrawerOpen(!drawerOpen);
  };

  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed">
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={toggleDrawer}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div">
            NFL Pick'em
          </Typography>
        </Toolbar>
      </AppBar>

      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={toggleDrawer}
      >
        <List>
          {menuItems.map((item) => (
            <ListItem
              button
              key={item.text}
              onClick={() => {
                toggleDrawer();
                // Add navigation logic here
              }}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItem>
          ))}
        </List>
      </Drawer>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: '100%',
          mt: 8,
        }}
      >
        <Routes>
          <Route
            path="/"
            element={
              <PrivateRoute>
                <Leaderboard />
              </PrivateRoute>
            }
          />
          <Route
            path="/picks"
            element={
              <PrivateRoute>
                <WeeklyPicks />
              </PrivateRoute>
            }
          />
          <Route
            path="/stats"
            element={
              <PrivateRoute>
                <Statistics />
              </PrivateRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <PrivateRoute>
                <Settings />
              </PrivateRoute>
            }
          />
          <Route path="/login" element={<Login />} />
        </Routes>
      </Box>
    </Box>
  );
}

export default function AppWithAuth() {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}
