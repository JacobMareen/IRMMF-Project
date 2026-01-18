import { Link } from 'react-router-dom'

const NotFound = () => {
  return (
    <section>
      <h1>Page Not Found</h1>
      <p>
        The route you requested does not exist. Return to the{' '}
        <Link to="/">Command Center</Link>.
      </p>
    </section>
  )
}

export default NotFound
