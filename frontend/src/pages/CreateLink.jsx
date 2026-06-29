import CreateLinkForm from '../components/CreateLinkForm'

// Page 1: create a short link (the owner comes from the JWT).
export default function CreateLink() {
  return (
    <div>
      <CreateLinkForm onCreated={() => {}} />
    </div>
  )
}
