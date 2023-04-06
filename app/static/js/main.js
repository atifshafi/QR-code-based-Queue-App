const { useState } = React;

function App() {
  const [name, setName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [validationErrors, setValidationErrors] = useState({});

  const handleSubmit = (event) => {
    event.preventDefault();
    const errors = {};

    if (name.trim() === '') {
      errors.name = 'Name is required';
    }

    const phoneNumberPattern = /^(\+?\d{1,4}[\s-]?)?(\d{1,8}[\s-]?){1,7}\d$/;
    if (!phoneNumberPattern.test(phoneNumber.trim())) {
      errors.phoneNumber = 'Please enter a valid phone number';
    }

    setValidationErrors(errors);

    if (Object.keys(errors).length === 0) {
      // submit form
    }
  };

  return (
    <div className="container">
      <div className="row">
        <div className="col-md-12">
          <h1 className="text-center">Welcome to Mehndi Magic!</h1>
          <p className="text-center">
            Please enter your name and phone number to join the queue.
          </p>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="name">Name:</label>
              <input
                type="text"
                className="form-control"
                id="name"
                name="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="phone_number">Phone Number:</label>
              <input
                type="tel"
                className="form-control"
                id="phone_number"
                name="phone_number"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                required
              />
            </div>
            <div className="form-group text-center">
              <button type="submit" className="btn btn-primary" id="join-queue-button">
                Join Queue
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

ReactDOM.render(<App />, document.getElementById('root'));
