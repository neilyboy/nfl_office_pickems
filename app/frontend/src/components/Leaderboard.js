import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
  Avatar,
  CircularProgress,
  Chip
} from '@mui/material';
import axios from 'axios';

function TabPanel({ children, value, index }) {
  return (
    <div hidden={value !== index} style={{ width: '100%' }}>
      {value === index && <Box sx={{ p: 2 }}>{children}</Box>}
    </div>
  );
}

export default function Leaderboard() {
  const [value, setValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [seasonData, setSeasonData] = useState([]);
  const [weeklyData, setWeeklyData] = useState([]);
  const [currentWeek, setCurrentWeek] = useState(1);

  useEffect(() => {
    fetchLeaderboardData();
  }, []);

  const fetchLeaderboardData = async () => {
    try {
      const [seasonResponse, weeklyResponse] = await Promise.all([
        axios.get('/api/leaderboard/season'),
        axios.get(`/api/leaderboard/weekly?week=${currentWeek}`)
      ]);
      setSeasonData(seasonResponse.data);
      setWeeklyData(weeklyResponse.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching leaderboard data:', error);
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setValue(newValue);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Tabs
        value={value}
        onChange={handleTabChange}
        variant="fullWidth"
        indicatorColor="primary"
        textColor="primary"
      >
        <Tab label="Season Overall" />
        <Tab label="Weekly Breakdown" />
      </Tabs>

      <TabPanel value={value} index={0}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Season Standings
            </Typography>
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Rank</TableCell>
                    <TableCell>Player</TableCell>
                    <TableCell align="center">Correct</TableCell>
                    <TableCell align="center">Weekly Wins</TableCell>
                    <TableCell align="center">Streak</TableCell>
                    <TableCell align="center">Accuracy</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {seasonData.map((player, index) => (
                    <TableRow key={player.id}>
                      <TableCell>{index + 1}</TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Avatar sx={{ width: 24, height: 24 }}>{player.username[0]}</Avatar>
                          {player.username}
                        </Box>
                      </TableCell>
                      <TableCell align="center">{player.correctPicks}</TableCell>
                      <TableCell align="center">{player.weeklyWins}</TableCell>
                      <TableCell align="center">
                        <Chip
                          label={`${player.streak} W`}
                          color={player.streak > 0 ? "success" : "default"}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="center">{`${(player.accuracy * 100).toFixed(1)}%`}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={value} index={1}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Week {currentWeek} Results
            </Typography>
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Rank</TableCell>
                    <TableCell>Player</TableCell>
                    <TableCell align="center">Correct</TableCell>
                    <TableCell align="center">MNF Points</TableCell>
                    <TableCell align="center">Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {weeklyData.map((player, index) => (
                    <TableRow key={player.id}>
                      <TableCell>{index + 1}</TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Avatar sx={{ width: 24, height: 24 }}>{player.username[0]}</Avatar>
                          {player.username}
                        </Box>
                      </TableCell>
                      <TableCell align="center">{player.weeklyCorrect}</TableCell>
                      <TableCell align="center">{player.mnfPrediction}</TableCell>
                      <TableCell align="center">
                        <Chip
                          label={player.status}
                          color={player.status === 'Winner' ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </TabPanel>
    </Box>
  );
}
