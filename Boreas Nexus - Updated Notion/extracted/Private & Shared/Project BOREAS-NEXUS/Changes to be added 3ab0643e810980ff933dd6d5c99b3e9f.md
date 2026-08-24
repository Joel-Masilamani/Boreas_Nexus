# Changes to be added

### 1. Define the AI models precisely

Replace generic terms like *AI*, *Physics-Informed AI*, and *Optimization* with the exact algorithms and explain why they were chosen.

### 2. Add a formal system architecture

Include a complete architecture diagram showing:

- Data sources
- Data pipeline
- Backend services
- AI modules
- Database
- APIs
- Dashboard
- Feedback loop

### 3. Make each module independently deployable

Treat every module as a microservice with its own API, inputs, outputs, and documentation.

### 4. Add a validation framework

Measure performance using:

- RMSE / MAE
- Prediction accuracy
- Recommendation effectiveness
- Simulation vs. real-world observations

### 5. Build a true decision-support platform

Instead of only recommending interventions, include:

- Cost estimation
- Expected temperature reduction
- Carbon reduction
- Energy savings
- ROI
- Confidence score

### 6. Add temporal forecasting

Support future scenario analysis such as:

- 2030 urban expansion
- Climate change effects
- Land-use changes
- "What-if" simulations

### 7. Include uncertainty estimation

Every prediction should include confidence intervals rather than a single value.

### 8. Improve documentation

Document:

- Data flow
- APIs
- Model training
- Dataset preprocessing
- Deployment
- User guide
- Technical report