import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  FormControl,
  Select,
  MenuItem,
  CircularProgress,
  Alert
} from '@mui/material';
import axios from 'axios';

export default function WeeklyPicks() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [week, setWeek] = useState(1);
  const [games, setGames] = useState([]);
  const [picks, setPicks] = useState({});

  useEffect(() => {
    fetchGames();
  }, [week]);

  const fetchGames = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`/api/picks?week=${week}`);
      setGames(response.data.games || []);
      setPicks(response.data.picks || {});
      setLoading(false);
    } catch (error) {
      console.error('Error fetching games:', error);
      setError('Failed to load games. Please try again later.');
      setLoading(false);
    }
  };

  const handlePickChange = async (gameId, team) => {
    try {
      await axios.post('/api/picks', {
        game_id: gameId,
        picked_team: team,
        week: week
      });
      
      // Update local state
      setPicks(prev => ({
        ...prev,
        [gameId]: team
      }));
    } catch (error) {
      console.error('Error saving pick:', error);
      setError('Failed to save pick. Please try again.');
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Card>
        <CardContent>
          <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h5" component="h2">
              Week {week} Picks
            </Typography>
            <FormControl sx={{ minWidth: 120 }}>
              <Select
                value={week}
                onChange={(e) => setWeek(e.target.value)}
                size="small"
              >
                {[...Array(18)].map((_, i) => (
                  <MenuItem key={i + 1} value={i + 1}>
                    Week {i + 1}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          {games.length === 0 ? (
            <Typography color="textSecondary">
              No games scheduled for Week {week}.
            </Typography>
          ) : (
            <Grid container spacing={2}>
              {games.map((game) => (
                <Grid item xs={12} key={game.id}>
                  <Card variant="outlined">
                    <CardContent>
                      <Grid container spacing={2} alignItems="center">
                        <Grid item xs={5}>
                          <Button
                            fullWidth
                            variant={picks[game.id] === game.away_team ? "contained" : "outlined"}
                            onClick={() => handlePickChange(game.id, game.away_team)}
                            color={picks[game.id] === game.away_team ? "primary" : "inherit"}
                          >
                            {game.away_team}
                          </Button>
                        </Grid>
                        <Grid item xs={2}>
                          <Typography align="center" color="textSecondary">
                            @
                          </Typography>
                        </Grid>
                        <Grid item xs={5}>
                          <Button
                            fullWidth
                            variant={picks[game.id] === game.home_team ? "contained" : "outlined"}
                            onClick={() => handlePickChange(game.id, game.home_team)}
                            color={picks[game.id] === game.home_team ? "primary" : "inherit"}
                          >
                            {game.home_team}
                          </Button>
                        </Grid>
                      </Grid>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
