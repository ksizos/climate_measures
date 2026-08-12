<section class="space-y-6">

    <header>

        <h2 class="text-lg font-medium text-gray-900">
            {{ __('Delete Account') }}
        </h2>

        <p class="mt-1 text-sm text-gray-600">
            {{ __('Once your account is deleted, all of its resources and data will be permanently deleted. Before deleting your account, please download any data or information that you wish to retain.') }}
        </p>

    </header>


    <button
        type="button"
        class="btn btn-danger"
        data-bs-toggle="modal"
        data-bs-target="#confirmUserDeletionModal">
        {{ __('Delete Account') }}
    </button>


    <div
        class="modal fade"
        id="confirmUserDeletionModal"
        tabindex="-1"
        aria-labelledby="confirmUserDeletionModalLabel"
        aria-hidden="true">

        <div class="modal-dialog modal-dialog-centered">

            <div class="modal-content">

                <form
                    method="POST"
                    action="{{ route('profile.destroy') }}">

                    @csrf
                    @method('DELETE')


                    <div class="modal-header">

                        <h5
                            class="modal-title"
                            id="confirmUserDeletionModalLabel">
                            {{ __('Are you sure you want to delete your account?') }}
                        </h5>


                        <button
                            type="button"
                            class="btn-close"
                            data-bs-dismiss="modal"
                            aria-label="Close"></button>

                    </div>


                    <div class="modal-body">

                        <p class="mt-1 text-sm text-gray-600">
                            {{ __('Once your account is deleted, all of its resources and data will be permanently deleted. Please enter your password to confirm you would like to permanently delete your account.') }}
                        </p>


                        <div class="mt-3">

                            <label
                                for="delete_user_password"
                                class="form-label">
                                {{ __('Password') }}
                            </label>


                            <input
                                id="delete_user_password"
                                name="password"
                                type="password"
                                class="form-control"
                                placeholder="{{ __('Password') }}"
                                autocomplete="current-password">


                            @if ($errors->userDeletion->has('password'))

                            <div class="mt-2 text-danger">
                                {{ $errors->userDeletion->first('password') }}
                            </div>

                            @endif

                        </div>

                    </div>


                    <div class="modal-footer">

                        <button
                            type="button"
                            class="btn btn-secondary"
                            data-bs-dismiss="modal">
                            {{ __('Cancel') }}
                        </button>


                        <button
                            type="submit"
                            class="btn btn-danger">
                            {{ __('Delete Account') }}
                        </button>

                    </div>

                </form>

            </div>

        </div>

    </div>

</section>


@if ($errors->userDeletion->isNotEmpty())

<script>
    document.addEventListener("DOMContentLoaded", () => {
        const modalElement =
            document.getElementById(
                "confirmUserDeletionModal"
            );

        if (!modalElement) {
            return;
        }

        const modal =
            bootstrap.Modal.getOrCreateInstance(
                modalElement
            );

        modal.show();
    });
</script>

@endif
