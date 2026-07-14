"""HTTP handlers for profile details and private profile images."""

from flask import Response, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.controllers.form_helpers import flash_form_errors
from app.forms.profile import ProfileForm
from app.repositories import user_repository
from app.utils.audit import log_audit
from app.utils.decorators import recent_reauthentication_required_for_writes


@login_required
@recent_reauthentication_required_for_writes
def edit():
    form = ProfileForm(obj=current_user)
    if not form.validate_on_submit():
        if request.method == "POST":
            flash_form_errors(form)
        return render_template("profile/edit.html", form=form)

    email = form.email.data.strip().lower()
    if user_repository.email_in_use(email, exclude_user_id=current_user.id):
        flash("That email is already used by another account.", "danger")
        return render_template("profile/edit.html", form=form)

    validated_upload = getattr(form.profile_image, "validated_upload", None)
    image = validated_upload.to_profile_image() if validated_upload else None

    user_repository.update_profile(
        user_id=current_user.id,
        display_name=form.display_name.data.strip(),
        email=email,
        profile_bio=form.profile_bio.data.strip() if form.profile_bio.data else "",
        image=image,
    )
    log_audit("profile_updated", "User updated profile information")
    flash("Profile updated successfully.", "success")
    return redirect(url_for("profile.edit"))


@login_required
def picture(image_hash):
    if image_hash != current_user.profile_image:
        abort(404)
    image = user_repository.find_owned_profile_image(current_user.id, image_hash)
    if not image or not image.image_data:
        abort(404)
    return Response(
        image.image_data,
        mimetype=image.mime_type,
        headers={
            "Content-Length": str(image.byte_size or len(image.image_data)),
            "Content-Disposition": "inline",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, max-age=300",
        },
    )
