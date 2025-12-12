% =========================================================================
% BMS SoC Estimation - Validation Script
% Author: Carlos Eduardo
% Description: Replicates the Python EKF logic to validate numerical accuracy.
% =========================================================================

clc; clear; close all;

%% 1. Parameters (Must match Python Code)
R0 = 0.01;
R1 = 0.005;
C1 = 3000;
Q_Ah = 3.0;
Q_total = Q_Ah * 3600; % Coulombs
dt = 0.5;
tau = R1 * C1;

% Simulation Time
T_total = 1000;
steps = T_total / dt;
t = 0:dt:(T_total-dt);

%% 2. Generate Synthetic Profile (Same as Python)
% Current profile: Sine wave + Noise
current_profile = 4 * sin(0.05 * t) + 0.5 * randn(size(t));

%% 3. Initialization
% True Battery State
soc_true = 0.8; 
v_c1_true = 0;

% EKF Estimation State (Intentional Error)
x_hat = [0.5; 0]; % [SoC; Vc1] - Starts at 50%
P = diag([0.1, 0.1]); 
Q = diag([1e-5, 1e-4]);
R = 0.1;

% Storage vectors
soc_history_true = zeros(1, steps);
soc_history_est = zeros(1, steps);
voltage_history = zeros(1, steps);

%% 4. Main Loop
fprintf('Running MATLAB Simulation...\n');

for k = 1:steps
    I = current_profile(k);
    
    % --- A. Physics Simulation (The Real Battery) ---
    % Update SoC
    soc_true = soc_true - (I * dt / Q_total);
    soc_true = max(0, min(1, soc_true)); % Clip
    
    % Update Vc1 (Discrete RC)
    alpha = exp(-dt/tau);
    v_c1_true = v_c1_true * alpha + R1 * I * (1 - alpha);
    
    % Calculate Terminal Voltage
    ocv_true = get_ocv(soc_true);
    v_true = ocv_true - v_c1_true - I * R0;
    
    % Add Sensor Noise
    v_measured = v_true + 0.01 * randn(); 
    
    % --- B. EKF Algorithm ---
    % 1. Predict (Time Update)
    x_hat(1) = x_hat(1) - (I * dt / Q_total);
    x_hat(2) = x_hat(2) * alpha + R1 * I * (1 - alpha);
    
    A = [1, 0; 0, alpha];
    P = A * P * A' + Q;
    
    % 2. Update (Measurement Update)
    soc_est = x_hat(1);
    ocv_est = get_ocv(soc_est);
    d_ocv = get_ocv_deriv(soc_est);
    
    z_hat = ocv_est - x_hat(2) - I * R0;
    y = v_measured - z_hat; % Innovation
    
    H = [d_ocv, -1];
    S = H * P * H' + R;
    K = (P * H') / S;
    
    x_hat = x_hat + K * y;
    P = (eye(2) - K * H) * P;
    
    % Store Data
    soc_history_true(k) = soc_true;
    soc_history_est(k) = x_hat(1);
    voltage_history(k) = v_measured;
end

%% 5. Visualization
figure('Color', 'w');

subplot(2,1,1);
plot(t, voltage_history, 'b');
grid on;
title('Measured Voltage (Simulated)');
ylabel('Voltage [V]');

subplot(2,1,2);
plot(t, soc_history_true, 'g', 'LineWidth', 2); hold on;
plot(t, soc_history_est, 'r--', 'LineWidth', 2);
grid on;
legend('True SoC', 'EKF Estimate');
title('SoC Estimation: Python Logic Validated in MATLAB');
ylabel('SoC');
xlabel('Time [s]');

fprintf('Simulation Complete.\n');

%% 6. Local Functions (Helper)
function v = get_ocv(s)
    % Simplified OCV curve (Must match Python _get_ocv)
    v = 3.0 + (s * 1.2);
    if s > 0.9
        v = v + 0.15 * (s - 0.9);
    elseif s < 0.1
        v = v - 0.15 * (0.1 - s);
    end
end

function d = get_ocv_deriv(s)
    % Derivative of the OCV curve
    d = 1.2;
    if s > 0.9
        d = d + 2.0; % High slope at top
    elseif s < 0.1
        d = d + 2.0; % High slope at bottom
    end
end